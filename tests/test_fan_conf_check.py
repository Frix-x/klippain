"""Tests for the _INIT_CHECKFANCONF startup macro.

Verifies that the startup check correctly detects the M106/M107 silent-ignore
misconfiguration: a [fan] section exists, a [gcode_macro M106] is defined,
but M106.1 is not available (no fan_bridge.cfg loaded).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STARTUP_CFG = REPO_ROOT / "macros" / "miscs" / "startup.cfg"
FAN_BRIDGE_CFG = REPO_ROOT / "macros" / "hardware_functions" / "fan_bridge.cfg"
AUX_FAN_CFG = REPO_ROOT / "macros" / "hardware_functions" / "aux_fan.cfg"


class TestInitCheckFanConfExists(unittest.TestCase):
    """Verify _INIT_CHECKFANCONF macro is defined and called at startup."""

    def setUp(self) -> None:
        self.startup_text = STARTUP_CFG.read_text(encoding="utf-8")

    def test_macro_is_defined(self) -> None:
        assert "[gcode_macro _INIT_CHECKFANCONF]" in self.startup_text

    def test_macro_is_called_at_startup(self) -> None:
        # Must appear inside _KLIPPAIN_STARTUP, after _INIT_CHECKPROBECONF
        startup_macro = self.startup_text.split("[gcode_macro _KLIPPAIN_STARTUP]")[1]
        assert "_INIT_CHECKFANCONF" in startup_macro

    def test_check_comes_after_probe_check(self) -> None:
        probe_pos = self.startup_text.find("_INIT_CHECKPROBECONF")
        fan_pos = self.startup_text.find("_INIT_CHECKFANCONF")
        assert probe_pos > 0, "_INIT_CHECKPROBECONF not found"
        assert fan_pos > probe_pos, "_INIT_CHECKFANCONF should come after _INIT_CHECKPROBECONF"


class TestInitCheckFanConfLogic(unittest.TestCase):
    """Verify the detection logic in _INIT_CHECKFANCONF checks the right conditions."""

    def setUp(self) -> None:
        self.startup_text = STARTUP_CFG.read_text(encoding="utf-8")
        # Extract the _INIT_CHECKFANCONF macro body
        match = re.search(
            r"\[gcode_macro _INIT_CHECKFANCONF\]\s*gcode:\s*(.*?)(?=\n\[gcode_macro|\Z)",
            self.startup_text,
            re.S,
        )
        assert match is not None, "_INIT_CHECKFANCONF macro body not found"
        self.macro_body = match.group(1)

    def test_checks_native_fan_section(self) -> None:
        assert "printer.configfile.settings.fan" in self.macro_body

    def test_checks_gcode_macro_m106(self) -> None:
        assert "gcode_macro M106" in self.macro_body

    def test_checks_m106_1_command(self) -> None:
        assert "M106.1" in self.macro_body

    def test_raises_error_on_misconfiguration(self) -> None:
        assert "action_raise_error" in self.macro_body

    def test_error_message_mentions_fan_bridge_cfg(self) -> None:
        assert "fan_bridge.cfg" in self.macro_body

    def test_error_message_mentions_silent_ignore(self) -> None:
        assert "silently ignored" in self.macro_body

    def test_logic_is_conjunction(self) -> None:
        # The macro should only raise when ALL three conditions are true:
        # has_native_fan AND has_gcode_m106 AND NOT has_m106_1
        assert "has_native_fan and has_gcode_m106 and not has_m106_1" in self.macro_body


class TestFanBridgeComment(unittest.TestCase):
    """Verify fan_bridge.cfg header reflects the startup validation."""

    def setUp(self) -> None:
        self.bridge_text = FAN_BRIDGE_CFG.read_text(encoding="utf-8")

    def test_mentions_startup_validation(self) -> None:
        assert "startup" in self.bridge_text.lower()

    def test_no_longer_suggests_manual_include_as_only_option(self) -> None:
        # The old comment said "add this include in your printer.cfg"
        # The new comment should mention that Klippain validates at startup
        assert "validates this at startup" in self.bridge_text.lower() or \
               "validates" in self.bridge_text.lower()


class TestAuxFanComment(unittest.TestCase):
    """Verify aux_fan.cfg header reflects the startup validation."""

    def setUp(self) -> None:
        self.aux_text = AUX_FAN_CFG.read_text(encoding="utf-8")

    def test_mentions_startup_validation(self) -> None:
        assert "startup" in self.aux_text.lower()

    def test_no_longer_says_silently_ignored(self) -> None:
        # The fallback comment should not say "silently ignored" anymore
        fallback_section = self.aux_text.split("Fallback M106/M107")[1] if "Fallback M106/M107" in self.aux_text else ""
        assert "silently ignored" not in fallback_section


if __name__ == "__main__":
    unittest.main()
