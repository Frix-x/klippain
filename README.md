# Generic Klipper configuration

This is a global generic Klipper config dedicated to be used on CoreXY printers (and perhaps others with some minor modifications). It's currently used on all my own machines: a Voron V2.4 (V2.1237), a Voron Trident, a custom TriZero, and a heavily modified Prusa i3 MK3s. Other Voron owners have also reported using this config as-is without any problems.

Please keep in mind this is a WIP and the files are beeing updated frequently with new custom features, PRs merged from users or just if I want to. **Do not** take it as a fully compliant config for every machines: look, think, understand and adapt it to your own.

You can reach out in the Voron Discord: i'm **Frix_x#0161**.


## Features

This config is designed to be generic. You can use it on a lot of machines by selecting and enabling the hardware options you need. This also activate automatically the associated macros and process under the hood.

I also tried, when possible, to put all the print settings directly in the Klipper config. My utlimate goal would be to be able to use the same Gcode file (sliced generically) with multiple materials or even share it across multiple printers. That's why I'm use and set firmware retraction in the macros, set pressure advance in the macros, etc...

This config is also known for the **adaptive bed mesh** functionnality that I wrote some time ago, the **custom calibrations macros** for pressure advance, flow, etc..., the **automated input shaper workflow**, and the **vibrations measurements** macros and scripts.

To get more info, you can find a [list with the details and usage instruction for all the features](./docs/features.md) in the docs folder. There is also for each, some custom install instructions if you want to install them as standalone in your own config and don't want to use this full generic config folder.


## Installation

The install of this config folder should not be too complicated if you are already familiar with the klipper configuration system. Here are the steps:
  1. Use an SSH connection to connect to your printer
  1. Check if you already have a `config` folder in the `~/printer_data` directory and remove it (or rename it to keep a backup).
  2. Clone this config in the `~/printer_data/config` directory. You can use the following command:

     ```
     git clone https://github.com/Frix-x/klipper-voron-V2.git ~/printer_data/config
     ```
  
  3. Open and configure the `printer.cfg` file: you just need to uncomment the lines that suit your printer hardware configuration. Basically start by selecting the board_pins coresponding to your MCU, then select the components used and software config needed (such as extruder type, XY motors, Z motors, QGL vs Z_TILT, etc...).
  4. Then, open the selected `board_pins` file in the `config/mcus` folder and add your MCU(s) serial port(s). Please follow the [official klipper documentation](https://www.klipper3d.org/FAQ.html#wheres-my-serial-port) to find it.
  5. Check your wiring and verify that the selected `board_pins` file is correct. See [pinout.md](./docs/pinout.md) for more info
  6. Now, open all the selected files in your `printer.cfg` and check that the pins are ok for your machine (regarding the board prefix name, the direction `!`, the pull-ups `^` or pull-downs `~`). Note: this step is necessary because of a current Klipper limitation that doesn't allow me to put these symbols directly in the board_pins files... I'm still looking for alternatives.
  7. Also, in the same way, open all the selected files in your `printer.cfg` and check the dimensions, the limits, the currents, and all the other values in every config sections. **Pay a special attention to the axis limits** in the `[stepper_...]` sections from the files located in [config/hardware/XY](./config/hardware/XY/) or [config/hardware/Z](./config/hardware/Z/). Also check the thermistor types in `[extruder]` and `[heated_bed]`, size of the plate in `[bed_mesh]`, etc... Note: this step is necessary because of a current Klipper limitation that doesn't allow the use of variables in the config files... I'm still looking for alternatives.
  8. Modify and adapt the `variables.cfg` file to suit the configuration of your machine. This file helps to configure and customize how all the macros should behave (coordinates of everythings, enabling/disabling software features, etc...).
  9. **Check very carefully all the features! This step is very important to avoid any problem on your machine.** You can start by following the [config checks from the official Klipper documentation](https://www.klipper3d.org/Config_checks.html). Then also verify that you are able to attach/detach the mechanical probe, do the QGL/Z_TILT, have the correct coordinates for all the used components (purge bucket, physical Z endstop, etc...). You should also verify your first layer calibration (and the `switch_offset` parameter from the automatic z calibration plugin if using it), etc...
  10. Finally when everything looks to be working, you need to add the custom print start gcode in your slicer. Here is an example for SuperSlicer:
     
      ```
      START_PRINT EXTRUDER_TEMP={first_layer_temperature[initial_extruder] + extruder_temperature_offset[initial_extruder]} BED_TEMP=[first_layer_bed_temperature] MATERIAL=[filament_type] CHAMBER=[chamber_temperature] SIZE={first_layer_print_min[0]}_{first_layer_print_min[1]}_{first_layer_print_max[0]}_{first_layer_print_max[1]}
      ```
     
      Also add to your custom print end gcode in your slicer:

      ```
      END_PRINT
      ```


## Sponsor the work

I try to stay open to any user needs if it suit and fit this config design. Please open an issue or a PR if you want a specific hardware device or new functionnalities to be supported.

Also, feel free to buy me a coffee or help me buy new hardware to support them in this config :)
