# Configuration of Klippain

Klippain requires a few simple steps to configure and customize it for your printer: please follow the following documentation step by step in order to get your printer running.

  > **Warning**:
  >
  > General rule to keep the auto-update feature working: **never modify Klippain files directly**, but instead add overrides as per the following documentation. To proceed, you can modify all the pre-installed templates in your config root folder (`printer.cfg`, `mcu.cfg`, `variables.cfg` and `overrides.cfg` and, if applicable, the MMU configs files in the `mmu` directory created when you install Happy-Hare) as they will be preserved on update.

## 1. MCU Settings

Before configuring Klippain, you will need to configure your MCUs and wiring. If you didn't select any templates during the installation (or want to customize the default wiring), modify your `mcu.cfg` file according to the [MCU pinout and wiring documentation](./pinout.md).

Don't forget to fill in the serial_port or can_uuid of your MCUs. Refer to the [official Klipper documentation](https://www.klipper3d.org/FAQ.html#wheres-my-serial-port) for help.

## 2. Printer Settings, Overrides, and Variables

Don't overlook, this section is the most important. Now that your MCU is configured, you will need to follow some additionnal steps to configure Klippain:

  1. In `printer.cfg`, uncomment lines corresponding to your printer hardware or software components to enable them (e.g., extruder type, XY motors, Z motors, QGL vs Z_TILT, etc.).
  1. Then, edit `overrides.cfg` according to the [overrides documentation and examples](./overrides.md). Use overrides to tweak machine dimensions, invert motor directions, change axis limits, currents, sensors type, or anything you feel the need to change.
  1. Once Klipper boots successfully, adjust the `variables.cfg` file to match your machine's configuration. This file provides additional customization for macro behavior (coordinates, enabling/disabling software features, etc.).

  > **Note**:
  >
  > If you want to use an MMU/ERCF with Klippain, you need to install the [HappyHare](https://github.com/moggieuk/Happy-Hare) backend. Also, have a look at the Klippain [MMU documentation](./docs/mmu.md) for more specific details about its configuration.

## 3. Initial startup of the machine

Before your first print, **carefully check all features to prevent issues on your machine!** Begin with the [config checks section from the official Klipper documentation](https://www.klipper3d.org/Config_checks.html).

Next, ensure the mechanical probe (if used) can be attached/detached, verify that QGL/Z_TILT works, and confirm correct coordinates for all components (purge bucket, physical Z endstop, etc.). Check your first layer calibration (and the `switch_offset` parameter of the automatic Z calibration plugin, if used), etc...

## 4. Slicer configuration

Klippain will work out of the box with most slicers on the market and your profiles should be almost ready to go. You will just need to set some custom start print and end print gcodes to give Klippain the correct info.

### Custom print start Gcode

| Slicer | Custom start print gcode |
|:-------|:-------------------------|
|[SuperSlicer](https://github.com/supermerill/SuperSlicer)|`START_PRINT EXTRUDER_TEMP={first_layer_temperature[initial_extruder] + extruder_temperature_offset[initial_extruder]} BED_TEMP=[first_layer_bed_temperature] MATERIAL=[filament_type] SIZE={first_layer_print_min[0]}_{first_layer_print_min[1]}_{first_layer_print_max[0]}_{first_layer_print_max[1]} INITIAL_TOOL={initial_extruder}`|
|[OrcaSlicer](https://github.com/SoftFever/OrcaSlicer)|`START_PRINT EXTRUDER_TEMP=[nozzle_temperature_initial_layer] BED_TEMP=[bed_temperature_initial_layer_single] MATERIAL=[filament_type] SIZE={first_layer_print_min[0]}_{first_layer_print_min[1]}_{first_layer_print_max[0]}_{first_layer_print_max[1]} INITIAL_TOOL=[initial_tool]`|
|[PrusaSlicer](https://github.com/prusa3d/PrusaSlicer)|`START_PRINT EXTRUDER_TEMP={first_layer_temperature[initial_extruder]} BED_TEMP=[first_layer_bed_temperature] MATERIAL=[filament_type] SIZE={first_layer_print_min[0]}_{first_layer_print_min[1]}_{first_layer_print_max[0]}_{first_layer_print_max[1]} INITIAL_TOOL={initial_extruder}`|

In addition, there are a few other optional parameters that are supported in Klippain (they must be added on the same line after the first parameters):
  - `CHAMBER=[chamber_temperature]` *(for SuperSlicer and OrcaSlicer)* or `CHAMBER=[idle_temperature]` *(for PrusaSlicer)* to set a target heatsoak temperature during the START_PRINT sequence.
  - `TOTAL_LAYER=[total_layer_count]` to be able to set the PRINT_STATS_INFOS in Klipper. If you use this, you will also need to add the corresponding `SET_PRINT_STATS_INFO CURRENT_LAYER={layer_num}` to your slicer custom layer change gcode.
  - `TOOLS_USED=!referenced_tools!` *(only for MMU users)* is highly recommended to check only the used tools with the HappyHare [Moonraker gcode preprocessor](https://github.com/moggieuk/Happy-Hare/blob/main/doc/gcode_preprocessing.md).
  - `CHECK_GATES=0` or `1` *(only for MMU users)* that will override the corresponding variable defined in Klippain `variables.cfg` for this specific print.
  - `SYNC_MMU_EXTRUDER=1` *(only for MMU users)* if you want to stay with the default `sync_to_extruder: 0` value of HappyHare (defined in `mmu/mmu_parameters.cfg`), but still want to use the sync for a specific print.


### Custom print start Gcode

All slicers will be happy with a simple:
```
END_PRINT
```

In addition, there are a few other optional parameters that are supported in Klippain (they must be added on the same line after the first parameters):
  - `FILTER_TIME=600` that will override the corresponding variable defined in Klippain `variables.cfg` for this specific print. Time is expressed in seconds.
  - `MMU_UNLOAD_AT_END=0` or `1` *(only for MMU users)* that will override the corresponding variable defined in Klippain `variables.cfg`.
