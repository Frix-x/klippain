# Overrides details

In Klipper, when two identical `[section]` are defined, it's the last one in the include order that will take over. Additionally, any missing values are filled in by the last entry. This mechanism is called an "override".

To keeps Klippain files read-only and compatible with Moonraker's update manager, you will need to use this mechansim extensively. There is default values included in every Klippain files, but if you want to change them, you can add some overrides without having to dig and modify all the files in Klippain folders.

Use overrides to tweak machine dimensions, invert motor directions, change axis limits, currents, sensors type, or anything you feel the need to change. You can even override a full macro to replace it completely by your own or add new features to Klippain on your side. This is a very powerful feature!

  > **Note**
  >
  > Klipper does not allow `[board_pins]` sections to contain pin modifiers such as `!`, `^`, and `~`. Furthermore, when configuring multiple MCUs simultaneously, all aliases used in hardware sections must be prefixed with the MCU name. This is a current limitation of Klipper and the reason why you'll also need to use the `overrides.cfg` file to add them.


## Common overrides

Since my defaults aim to be as generic as possible, you won't need many overrides. However, there are still some common elements to check.

For example, **pay special attention to axis limits** in the `[stepper_...]` sections, run current, etc. Verify thermistor types in `[extruder]` and `[heater_bed]` sections. If using a multi-MCU configuration, you'll need to override any section where pins are connected to the secondary or toolhead boards to specify it. Finally, use overrides if you want to change motor direction or add a pull-up/down (using `!`, `^`, and `~`).

Additionally, if you want to add a new macro to Klippain or even replace an existing one to adapt it to your use case, you can do it the same way!


## How to write an override

The following examples should help you add all the overrides you need to customize Klippain and make it work correctly with your printer!

If something in your hardware isn't working as expected, first inspect the relevant default configuration file for your hardware. For example if your v0 display encoder is rotating in the opposite direction:
`cd ~/printer_data/config` then `less config/hardware/displays/V0_display.cfg`, copy the relevant portion then edit to suit in your `overrides.cfg`:
```
[display]
# Set the direction of the encoder wheel
#   Standard: Right (clockwise) scrolls down or increases values. Left (counter-clockwise scrolls up or decreases values.
#encoder_pins: ^v0_display:PA3, ^v0_display:PA4
#   Reversed: Right (clockwise) scrolls up or decreases values. Left (counter-clockwise scrolls down or increases values.
encoder_pins: ^v0_display:PA4, ^v0_display:PA3
```

Or let's say you want to change the motor current for the X-axis. You'll need to override the `[tmc2209 stepper_x]` section because that's where the current is defined. To do this, simply add the following to your `overrides.cfg` file:
```
[tmc2209 stepper_x]
run_current: ...
```

Similarly, if you want to invert the Z2 motor direction, override the `[stepper_z2]` section and add a `!` before the pin name:
```
[stepper_z2]
dir_pin: !mcu:Z2_DIR
```

Changing a thermistor type (like for the bed), can be done this way:
```
[heater_bed]
sensor_type: ...
```

You can even redefine a full macro! For example if the default Klippain prime line is not adapted to your needs, just override the macro like that:
```
[gcode_macro _MODULE_PRIMELINE]
gcode:
  # Put your custom prime line G-code here...
```
