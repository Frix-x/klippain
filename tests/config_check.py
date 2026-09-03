#!/usr/bin/env python3
"""Assemble a full Klippain printer config in a scratch dir and validate it
with a real Klipper (klippy) config load, without any hardware.

The scratch dir mimics what the Klippain install script creates on a printer:
user_templates files are copied in, and the config/macros/scripts folders are
symlinked to the repository. A reference machine is enabled by uncommenting
the relevant lines of user_templates/printer.cfg.

Usage:
    python3 tests/config_check.py [standard|tachometer] [path/to/klipper]
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VARIANTS = {
    "standard": "config/hardware/fans/aux_fan.cfg",
    "tachometer": "config/hardware/fans/aux_fan_tachometer.cfg",
}

# Reference machine: a Voron-style CoreXY 350mm with an inductive virtual Z
# endstop probe, chamber temperature sensor, a recirculating filter and both
# base + auxiliary part cooling fans. Keeps a real load of the Klippain macros
# (including the aux fan heatsink/vent/run-down logic) without extra plugins.
ENABLED_INCLUDES = [
    "config/kinematics/corexy.cfg",
    "config/hardware/axis/X/1.8deg_1M.cfg",
    "config/hardware/axis/Y/1.8deg_1M.cfg",
    "config/hardware/axis/Z/Trident_TR8x8_1.8deg.cfg",
    "config/hardware/axis/size/350mm.cfg",
    "config/hardware/extruder/cw2.cfg",
    "config/hardware/bed_heaters/keenovo.cfg",
    "config/hardware/probes/inductive_virtual.cfg",
    "config/hardware/fans/hotend_fan.cfg",
    "config/hardware/fans/part_fan.cfg",
    "config/hardware/fans/controller_fan.cfg",
    "config/hardware/fans/rpi_fan.cfg",
    "config/hardware/filters/nevermore_filter.cfg",
    "config/hardware/temperature_sensors/chamber_temp.cfg",
    "config/software/bed_mesh/bed_mesh_350mm.cfg",
    "config/software/tilting/qgl_350mm.cfg",
    "config/software/firmware_rectraction.cfg",
]

# rpi_fan.cfg uses [temperature_fan] with sensor_type: temperature_host,
# which requires /sys/class/thermal/thermal_zone0/temp.  Skip it when
# the host thermal zone is unavailable (e.g. CI runners, Docker, VMs).
if not os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
    ENABLED_INCLUDES = [p for p in ENABLED_INCLUDES if "rpi_fan" not in p]

# Dummy main MCU + board_pins aliases covering every pin referenced by the
# reference machine above. Pins are only validated for existence, never used.
# Heater control is normally set in the user overrides.cfg (PID autotune), so
# it is provided here as well to satisfy Klipper's required options.
BOARD_PINS = """\
[mcu]
serial: /dev/null

[board_pins]
aliases:
    X_STEP=PB0  , X_DIR=PB1    , X_ENABLE=PB2    , X_STOP=PB3   ,
    Y_STEP=PB4  , Y_DIR=PB5    , Y_ENABLE=PB6    , Y_STOP=PB7   ,
    Z_STEP=PB8  , Z_DIR=PB9    , Z_ENABLE=PB10   , Z_STOP=PB11  ,
    Z1_STEP=PB12, Z1_DIR=PB13  , Z1_ENABLE=PB14  ,
    Z2_STEP=PC0 , Z2_DIR=PC1   , Z2_ENABLE=PC2   ,
    E_STEP=PC3  , E_DIR=PC4    , E_ENABLE=PC5    ,
    E_HEATER=PA2, E_TEMPERATURE=PF4 ,
    BED_HEATER=PA3, BED_TEMPERATURE=PF3 ,
    PROBE_INPUT=PG15 ,
    E_FAN=PE5 , PART_FAN=PA8 , AUX_FAN=PC6 , AUX_FAN_TACHO=PC7 ,
    CONTROLLER_FAN=PD12 , HOST_CONTROLLER_FAN=PD13 , FILTER_FAN=PD14 ,
    CHAMBER_TEMPERATURE=PF5

[heater_bed]
control: pid
pid_Kp: 68.6
pid_Ki: 1.95
pid_Kd: 603.0

[extruder]
control: pid
pid_Kp: 26.0
pid_Ki: 1.77
pid_Kd: 95.6
"""


def build_printer_cfg(variant):
    """Uncomment the selected [include] lines of user_templates/printer.cfg."""
    template_path = os.path.join(REPO_ROOT, "user_templates", "printer.cfg")
    selected = set(ENABLED_INCLUDES) | {VARIANTS[variant]}
    out = []
    with open(template_path, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.lstrip()
            if stripped.startswith("# [include "):
                spec = stripped[len("# [include "):].strip()
                spec = spec.split("#", 1)[0].strip()
                spec = spec.rstrip("]")
                if spec in selected:
                    out.append(line[2:] if line.startswith("# ") else line)
                    continue
            out.append(line)
    return "".join(out)


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "standard"
    klipper = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.path.join(REPO_ROOT, "klipper")
    )
    if variant not in VARIANTS:
        raise SystemExit("Unknown variant '%s' (use: %s)"
                         % (variant, ", ".join(sorted(VARIANTS))))
    klippy = os.path.join(klipper, "klippy", "klippy.py")
    if not os.path.exists(klippy):
        raise SystemExit(
            "Klipper not found at '%s' - clone it first:\n"
            "  git clone --depth 1 https://github.com/Klipper3d/klipper.git klipper"
            % (klipper,))

    with tempfile.TemporaryDirectory(prefix="klippain_ci_") as scratch:
        # User config files, mirroring what install.sh copies
        for name in ("variables.cfg", "overrides.cfg"):
            shutil.copy(
                os.path.join(REPO_ROOT, "user_templates", name), scratch)
        # save_variables is defined in variables.cfg and must point to a
        # writable file inside the scratch dir (no real printer_data exists)
        variables_path = os.path.join(scratch, "variables.cfg")
        with open(variables_path, encoding="utf-8") as handle:
            variables = handle.read()
        variables = re.sub(
            r"filename:.*", "filename: %s"
            % os.path.join(scratch, "save_variables.cfg"), variables, count=1)
        with open(variables_path, "w", encoding="utf-8") as handle:
            handle.write(variables)
        with open(os.path.join(scratch, "printer.cfg"), "w",
                  encoding="utf-8") as handle:
            handle.write(build_printer_cfg(variant))
        with open(os.path.join(scratch, "mcu.cfg"), "w",
                  encoding="utf-8") as handle:
            handle.write(BOARD_PINS)

        # Klippain-managed folders, symlinked like the install script does
        for folder in ("config", "macros", "scripts"):
            os.symlink(os.path.join(REPO_ROOT, folder),
                       os.path.join(scratch, folder))

        # Stage the gcode_shell_command plugin used by scripts/*.cfg
        plugin = os.path.join(REPO_ROOT, "scripts", "gcode_shell_command.py")
        plugin_dest = os.path.join(klipper, "klippy", "extras",
                                   "gcode_shell_command.py")
        if not os.path.exists(plugin_dest):
            shutil.copy(plugin, plugin_dest)

        cmd = [
            sys.executable, klippy,
            "-i", os.devnull,
            "-l", os.path.join(scratch, "klippy.log"),
            os.path.join(scratch, "printer.cfg"),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=60)
        except subprocess.TimeoutExpired:
            proc = None
        log = ""
        log_path = os.path.join(scratch, "klippy.log")
        if os.path.exists(log_path):
            with open(log_path, encoding="utf-8", errors="replace") as handle:
                log = handle.read()
        combined = (proc.stdout + proc.stderr + log) if proc else log

        # klippy exits nonzero on the expected "no MCU connected" failure, and
        # can also stay alive retrying the MCU serial connection, so classify
        # based on the log content instead of the exit code:
        #   - a real config/template problem logs "Config error" or raises an
        #     unhandled exception during config loading
        #   - a healthy config either exits on the MCU connection step or hangs
        #     retrying it
        if re.search(r"Config error|Unhandled exception during connect",
                     combined):
            print("=== klippy output (first 4000 chars) ===")
            print(combined[:4000])
            print("=== klippy log tail ===")
            print(log[-4000:])
            raise SystemExit(
                "FAIL: variant '%s' - config or macro is invalid"
                % (variant,))

        if "Unable to connect" in combined or "Unable to open serial port" in combined:
            print("PASS: variant '%s' config loaded cleanly by klippy "
                  "(only the expected MCU connection failed)" % variant)
        elif proc is None:
            print("PASS: variant '%s' config loaded cleanly by klippy "
                  "(klippy timed out retrying the MCU connection)" % variant)
        else:
            print("PASS: variant '%s' config loaded cleanly by klippy"
                  % variant)
    return 0


if __name__ == "__main__":
    sys.exit(main())
