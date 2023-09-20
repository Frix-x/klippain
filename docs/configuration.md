# Configuration of Klippain

Klippain requires a few simple steps to configure and customize it for your printer: please follow the following documentation step by step in order to get your printer running.

  > **Warning**
  >
  > General rule to keep the auto-update feature working: **never modify Klippain files directly**, but instead add overrides as per the following documentation. To proceed, you can modify all the pre-installed templates in your config root folder (`printer.cfg`, `mcu.cfg`, `variables.cfg` and `overrides.cfg` and the MMU configs files in mmu directory created when you install Happy-Hare v2) as they will be preserved on update.


## 1. MCU Settings

Before configuring Klippain, you will need to configure your MCUs and wiring. If you didn't select any templates during the installation (or want to customize the default wiring), modify your `mcu.cfg` file according to the [MCU pinout and wiring documentation](./pinout.md).

Don't forget to fill in the serial_port or can_uuid of your MCUs. Refer to the [official Klipper documentation](https://www.klipper3d.org/FAQ.html#wheres-my-serial-port) for help.


## 2. Printer Settings, Overrides, and Variables

Don't overlook, this section is the most important. Now that your MCU is configured, you will need to follow some additionnal steps to configure Klippain:
  1. In `printer.cfg`, uncomment lines corresponding to your printer hardware or software components to enable them (e.g., extruder type, XY motors, Z motors, QGL vs Z_TILT, etc.).
  1. Then, edit `overrides.cfg` according to the [overrides documentation and examples](./overrides.md). Use overrides to tweak machine dimensions, invert motor directions, change axis limits, currents, sensors type, or anything you feel the need to change.
  1. Once Klipper boots successfully, adjust the `variables.cfg` file to match your machine's configuration. This file provides additional customization for macro behavior (coordinates, enabling/disabling software features, etc.).

  > **Important Note**:
  >
  > This branch of Klippain is for using with MMU/ERCF, it's only compatible with the [Happy Hare v2] (https://github.com/moggieuk/Happy-Hare.git) software backend.
  > by enable the MMU/ERCF lines in Klippain's `printer.cfg` and then install Happy Hare directly by following its official documention.
  > Take in mind that HHv2 use a new extruder section (define in `/mmu/base/mmu_hardware.cfg` file): especialy take care about `[tmc2209 manual_extruder_stepper extruder]` for replacement of `[tmc2209 extruder]` so **all the [tmc2209 extruder] section in klippain must be comment out (see in `mcu.cfg`)  and report in `[tmc2209 manual_extruder_stepper extruder]` section of mmu_hardware.cfg !!!**.
 **If the Happy Hare installer ask if you want to include all the MMU files into your printer.cfg: answer no** as everything is already included in Klippain!


## 3. Initial startup of the machine

Before your first print, **carefully check all features to prevent issues on your machine!** Begin with the [config checks section from the official Klipper documentation](https://www.klipper3d.org/Config_checks.html).

Next, ensure the mechanical probe (if used) can be attached/detached, verify that QGL/Z_TILT works, and confirm correct coordinates for all components (purge bucket, physical Z endstop, etc.). Check your first layer calibration (and the `switch_offset` parameter of the automatic Z calibration plugin, if used), etc.

Finally, add custom print start G-code to your slicer. Here's an example for SuperSlicer:  
```
START_PRINT EXTRUDER_TEMP={first_layer_temperature[initial_extruder] + extruder_temperature_offset[initial_extruder]} BED_TEMP=[first_layer_bed_temperature] MATERIAL=[filament_type] CHAMBER=[chamber_temperature] SIZE={first_layer_print_min[0]}_{first_layer_print_min[1]}_{first_layer_print_max[0]}_{first_layer_print_max[1]} INITIAL_TOOL={initial_extruder} TOOLS_USED=!referenced_tools!
```
Another example for OrcaSlicer:
```
START_PRINT EXTRUDER_TEMP=[nozzle_temperature_initial_layer] BED_TEMP=[bed_temperature_initial_layer_single] MATERIAL=[filament_type] CHAMBER=[chamber_temperature] SIZE={first_layer_print_min[0]}_{first_layer_print_min[1]}_{first_layer_print_max[0]}_{first_layer_print_max[1]} INITIAL_TOOL=[initial_tool] TOOLS_USED=!referenced_tools!
```

Also, add custom print end G-code to your slicer:
```
END_PRINT
```

  > **Note** for MMU/ERCF users:
  >
  > By default, Klippain unloads the filament at the end of the print, but you can change the default behavior by modifying the variable `variable_ercf_unload_on_end_print` in your `variables.cfg` file.
  > You can also specify the wanted behavior directly in your slicer end print custom gcode by using `END_PRINT MMU_UNLOAD_AT_END=0`.

