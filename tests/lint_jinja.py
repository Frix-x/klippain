#!/usr/bin/env python3
"""Jinja2 template syntax check for all Klippain gcode config files.

This catches template syntax errors in every [gcode_macro] / [delayed_gcode]
and other templated gcode blocks without needing a running Klipper instance.
It reuses the same Jinja2 delimiters Klipper uses, so a pass here matches what
klippy would accept at config load time.

Usage:
    python3 tests/lint_jinja.py
"""

import os
import re
import sys

import jinja2

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Options that Klipper renders through its Jinja2 engine
TEMPLATED_OPTIONS = {
    "gcode",
    "on_error_gcode",
    "start_gcode",
    "end_gcode",
    "on_gcode",
    "on_pause",
    "on_resume",
    "on_heating_error",
}

SKIP_DIRS = {".git", "mcu_defaults"}
SECTION_RE = re.compile(r"^\s*\[")
OPTION_RE = re.compile(r"^([A-Za-z0-9_]+)\s*:\s?(.*)$")


def iter_cfg_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        if SKIP_DIRS & set(dirpath.split(os.sep)):
            continue
        for name in filenames:
            if name.endswith(".cfg"):
                yield os.path.join(dirpath, name)


def parse_templated_blocks(text):
    """Yield (section, option, value, lineno) for each templated block."""
    lines = text.splitlines()
    section = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if SECTION_RE.match(line):
            section = line.strip()[1:-1].strip()
            i += 1
            continue
        match = OPTION_RE.match(line.lstrip())
        if match is not None and match.group(1) in TEMPLATED_OPTIONS:
            value_lines = [match.group(2)]
            j = i + 1
            while j < len(lines) and (
                lines[j] == "" or lines[j][:1] in (" ", "\t")
            ):
                value_lines.append(lines[j])
                j += 1
            yield section, match.group(1), "\n".join(value_lines), i + 1
            i = j
            continue
        i += 1


def main():
    env = jinja2.Environment("{%", "%}", "{", "}")
    errors = []
    checked = 0
    for fpath in iter_cfg_files(REPO_ROOT):
        with open(fpath, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        for section, option, value, lineno in parse_templated_blocks(text):
            checked += 1
            try:
                env.parse(value)
            except jinja2.TemplateSyntaxError as exc:
                relpath = os.path.relpath(fpath, REPO_ROOT)
                exc_line = lineno + (exc.lineno or 1) - 1
                errors.append(
                    "%s ([%s] %s, line %d): %s"
                    % (relpath, section, option, exc_line, exc.message)
                )

    if errors:
        print("Jinja2 syntax errors found:")
        for error in errors:
            print("  " + error)
        print("\n%d/%d templated blocks failed" % (len(errors), checked))
        return 1

    print("Jinja2 syntax OK: %d templated blocks checked" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
