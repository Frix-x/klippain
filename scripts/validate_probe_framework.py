#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path


VALID_MODES = {"none", "standard_g28", "hook"}
HOOK_MACROS = {
    "contact_z_home": "_PROBE_HOOK_CONTACT_Z_HOME",
    "contact_auto_calibrate": "_PROBE_HOOK_CONTACT_AUTO_CALIBRATE",
    "contact_activate": "_PROBE_HOOK_CONTACT_ACTIVATE",
    "contact_deactivate": "_PROBE_HOOK_CONTACT_DEACTIVATE",
}
BANNED_NAMES = {"cartographer_survey.cfg", "PZ Probe.cfg"}
REQUIRED_REPO_PATHS = {
    "README.md": "file",
    "config/machine.cfg": "file",
    "config/hardware/probes": "dir",
    "macros/base/probing": "dir",
    "scripts": "dir",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def variable(text: str, name: str, default: str = "") -> str:
    match = re.search(rf"^\s*variable_{re.escape(name)}\s*:\s*(.*?)\s*$", text, re.M)
    if not match:
        return default
    value = strip_inline_comment(match.group(1)).strip()
    try:
        return str(ast.literal_eval(value))
    except (SyntaxError, ValueError):
        return value


def strip_inline_comment(value: str) -> str:
    in_single_quote = False
    in_double_quote = False
    for index, char in enumerate(value):
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == "#" and not in_single_quote and not in_double_quote:
            return value[:index].strip()
    return value.strip()


def includes_hook(text: str, hook_family: str) -> bool:
    if not hook_family:
        return False
    return hook_family in hook_includes(text)


def hook_includes(text: str) -> list[str]:
    return re.findall(r"^\s*\[include\s+[^\]]*hooks/([A-Za-z0-9_-]+)\.cfg\s*\]\s*(?:#.*)?$", text, re.M)


def has_macro(text: str, macro: str) -> bool:
    return re.search(rf"^\s*\[gcode_macro\s+{re.escape(macro)}\]\s*(?:#.*)?$", text, re.M) is not None


def validate_repo_layout(repo: Path) -> list[str]:
    errors: list[str] = []
    if not repo.is_dir():
        return [f"repository root does not exist or is not a directory: {repo}"]

    for relative_path, expected_type in REQUIRED_REPO_PATHS.items():
        path = repo / relative_path
        if expected_type == "dir" and not path.is_dir():
            errors.append(f"required directory is missing: {path}")
        elif expected_type == "file" and not path.is_file():
            errors.append(f"required file is missing: {path}")

    return errors


def validate(repo: Path) -> list[str]:
    errors = validate_repo_layout(repo)
    if errors:
        return errors

    profiles_dir = repo / "config" / "hardware" / "probes"
    hooks_dir = repo / "macros" / "base" / "probing" / "hooks"

    for banned in BANNED_NAMES:
        if (profiles_dir / banned).exists():
            errors.append(f"unmerged PR compatibility alias must not exist: {profiles_dir / banned}")

    for profile in sorted(profiles_dir.glob("*.cfg")):
        text = read(profile)
        hook_family = variable(text, "probe_hook_family")
        needs_contact_guard = variable(text, "probe_needs_contact_temp_guard", "False").lower() == "true"
        z_home_mode = variable(text, "probe_contact_z_home_mode", "none")
        auto_cal_mode = variable(text, "probe_contact_auto_calibrate_mode", "none")
        declared_hook_includes = hook_includes(text)

        for mode_name, mode in {
            "probe_contact_z_home_mode": z_home_mode,
            "probe_contact_auto_calibrate_mode": auto_cal_mode,
        }.items():
            if mode not in VALID_MODES:
                errors.append(f"{profile}: {mode_name} has invalid value {mode!r}; valid values are {sorted(VALID_MODES)}")

        if hook_family and z_home_mode == "none" and auto_cal_mode == "none":
            errors.append(f"{profile}: hook family {hook_family!r} is set but both contact operation modes are none")

        if len(declared_hook_includes) > 1:
            errors.append(f"{profile}: includes multiple hook families {declared_hook_includes}; include exactly one hook family per profile")

        if hook_family and not includes_hook(text, hook_family):
            errors.append(f"{profile}: hook family {hook_family!r} is set but hooks/{hook_family}.cfg is not included")

        for included_hook in declared_hook_includes:
            included_hook_file = hooks_dir / f"{included_hook}.cfg"
            if not included_hook_file.exists():
                errors.append(f"{profile}: includes hooks/{included_hook}.cfg but {included_hook_file} does not exist")
            if hook_family != included_hook:
                errors.append(f"{profile}: includes hooks/{included_hook}.cfg but probe_hook_family is {hook_family!r}")

        hook_file = hooks_dir / f"{hook_family}.cfg" if hook_family else None
        hook_text = read(hook_file) if hook_file and hook_file.exists() else ""

        if z_home_mode == "hook":
            if not hook_file or not hook_file.exists():
                errors.append(f"{profile}: contact Z home uses hook mode but {hook_file} does not exist")
            elif not has_macro(hook_text, HOOK_MACROS["contact_z_home"]):
                errors.append(f"{profile}: contact Z home uses hook mode but {HOOK_MACROS['contact_z_home']} is missing")

        if auto_cal_mode == "hook":
            if not hook_file or not hook_file.exists():
                errors.append(f"{profile}: contact auto-calibrate uses hook mode but {hook_file} does not exist")
            elif not has_macro(hook_text, HOOK_MACROS["contact_auto_calibrate"]):
                errors.append(f"{profile}: contact auto-calibrate uses hook mode but {HOOK_MACROS['contact_auto_calibrate']} is missing")

        if hook_family and needs_contact_guard:
            if not hook_file or not hook_file.exists():
                errors.append(f"{profile}: contact guard uses hook family {hook_family!r} but {hook_file} does not exist")
            else:
                for lifecycle_name in ("contact_activate", "contact_deactivate"):
                    lifecycle_macro = HOOK_MACROS[lifecycle_name]
                    if not has_macro(hook_text, lifecycle_macro):
                        errors.append(f"{profile}: contact guard uses hook family {hook_family!r} but {lifecycle_macro} is missing")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Klippain virtual-Z probe framework contracts.")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root")
    args = parser.parse_args()

    errors = validate(args.repo.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("virtual-Z probe framework contracts OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
