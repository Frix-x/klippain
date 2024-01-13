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

## 3. Initial startup of the machine

  🔸 Before your first print, **carefully check all features to prevent issues on your machine!** Begin with the [config checks section from the official Klipper documentation](https://www.klipper3d.org/Config_checks.html).

  🔸 Next, ensure the mechanical probe (if used) can be attached/detached, verify that QGL/Z_TILT works, and confirm correct coordinates for all components (purge bucket, physical Z endstop, etc.). Check your first layer calibration (and the `switch_offset` parameter of the automatic Z calibration plugin, if used), etc.

  🔸 Then, add this base custom print start G-code to your slicer:  

- example for [**SuperSlicer**](https://github.com/supermerill/SuperSlicer) :

```
START_PRINT EXTRUDER_TEMP={first_layer_temperature[initial_extruder] + extruder_temperature_offset[initial_extruder]} BED_TEMP=[first_layer_bed_temperature] MATERIAL=[filament_type] SIZE={first_layer_print_min[0]}_{first_layer_print_min[1]}_{first_layer_print_max[0]}_{first_layer_print_max[1]} INITIAL_TOOL={initial_extruder}
```

- example for [**OrcaSlicer**](https://github.com/SoftFever/OrcaSlicer) :

```
START_PRINT EXTRUDER_TEMP=[nozzle_temperature_initial_layer] BED_TEMP=[bed_temperature_initial_layer_single] MATERIAL=[filament_type] CHAMBER=[chamber_temperature] SIZE={first_layer_print_min[0]}_{first_layer_print_min[1]}_{first_layer_print_max[0]}_{first_layer_print_max[1]} INITIAL_TOOL=[initial_tool]
```
example for [PrusaSlicer](https://github.com/prusa3d/PrusaSlicer) :
```
START_PRINT EXTRUDER_TEMP={first_layer_temperature[initial_extruder]} BED_TEMP=[first_layer_bed_temperature] MATERIAL=[filament_type] CHAMBER=[idle_temperature] SIZE={first_layer_print_min[0]}_{first_layer_print_min[1]}_{first_layer_print_max[0]}_{first_layer_print_max[1]} INITIAL_TOOL={initial_extruder}
```

- example for [**PrusaSlicer**](https://github.com/prusa3d/PrusaSlicer) :

```
START_PRINT EXTRUDER_TEMP={first_layer_temperature[initial_extruder]} BED_TEMP=[first_layer_bed_temperature] MATERIAL=[filament_type] CHAMBER=[idle_temperature] SIZE={first_layer_print_min[0]}_{first_layer_print_min[1]}_{first_layer_print_max[0]}_{first_layer_print_max[1]} INITIAL_TOOL={initial_extruder}
```

‎  
*There is also a couple of other optionnal parameters that are supported in Klippain (they need to be added on the same one line following the other parameters)*:

- **`CHAMBER=[chamber_temperature]`** (for SuperSlicer and OrcaSlicer) or **`CHAMBER=[idle_temperature]`** (for PrusaSlicer) to be able to specify a target heatsoak temperature for the START_PRINT sequence
- **`TOTAL_LAYER=[total_layer_count]`** to be able to set the PRINT_STATS_INFOS in Klipper. If using this, you will need to add on your slicer custom layer change gcode the appropriate `SET_PRINT_STATS_INFO CURRENT_LAYER={layer_num}`

  > **Note** for MMU/ERCF users:
  >
  > - **`TOOLS_USED=!referenced_tools!`** ***parameter is highly recommanded for the [HHv2 moonraker gcode preprocessor](https://github.com/moggieuk/Happy-Hare/blob/main/doc/gcode_preprocessing.md) to check only the used tools.***  
  >
  > Optionnaly: you can add:  
  >
  > - **`CHECK_GATES=0`** or **`1`** to be able to override the one define in Klippain `variables.cfg`.  
  > - **`SYNC_MMU_EXTRUDER=1`** in case you stay with default value for Happy Hare V2.x `sync_to_extruder: 0` variable define in `mmu_parameters.cfg`. And want to use it for particular print.

 🔸 Finally, add custom print end G-code to your slicer:

```
END_PRINT
```

  > **Note** for MMU/ERCF users:
  >
  > - **`MMU_UNLOAD_AT_END=0`** or **`1`** parameter: to be able to override the default `variable_mmu_unload_on_end_print` in your Klippain `variables.cfg` file.
