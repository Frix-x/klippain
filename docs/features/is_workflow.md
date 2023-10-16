# Input Shaper workflow

## Description

This standalone Klippain module is dedicated to automate and run custom input shaper tests on your machine and streamline the workflow. Here is how it works:
  1. Using custom Klipper macros, it run the tests either for the belts or the printer X/Y axis to measure the machine axes behavior using the ADXL345.
  2. Then, it call an automatic Python script that automate a few things:
     1. it generate some custom made graphs that should give you all the insights of what is happenning in your machine. The goal is to get the best set of parameters for the Klipper `[input_shaper]` system (including best shaper choice, resonant frequency and damping ratio), or diagnose and fix the mechanical problems like belt tension, etc...
     2. it then move the graphs and associated CSVs files to the [ADXL results folder](./../../adxl_results/) to allow you to find them easily using Mainsail/Fluidd (no more SSH is needed to calibrate your input shaper!)
     3. it manage the folder to delete the older files and keep only a set (default is three) of the most recent results.

If needed, you can get some hints on the results in my documentation about [how to read and interpret the IS graphs](../input_shaper.md).

| Belts resonances example | X resonances example | Y resonances example |
|:----------------------:|:----------------------:|:---------------------:|
| ![belts resonances example](./../images/resonances_belts_example.png) | ![X resonances example](./../images/resonances_x_example.png) | ![Y resonances example](./../images/resonances_y_example.png) |


## Installation

  > **Note**
  >
  > This input shaper workflow module is part of the [Klippain](https://github.com/Frix-x/klippain) ecosystem. So if you're already using a full Klippain installation on your machine, this is already included and you can already use it!

If you want to install it in your own config, then here are the steps:
  1. Copy the [IS_shaper_calibrate.cfg](./../../macros/calibration/IS_shaper_calibrate.cfg) and [IS_vibrations_measurement.cfg](./../../macros/calibration/IS_vibrations_measurement.cfg) macros directly into your own `printer.cfg` config.
  2. Be sure to have the `gcode_shell_command.py` Klipper extension installed. Easiest way to install it is to use the advanced section of KIAUH.
  3. Add the [is_workflow folder](./../../scripts/is_workflow/) at the root of your own config (ie. in your `~/printer_data/config/` directory).
  4. Make the scripts executable using SSH. When in the folder (`cd ~/printer_data/config/is_workflow`), use:

     ```bash
     chmod +x ./is_workflow.py
     chmod +x ./graph_belts.py
     chmod +x ./graph_shaper.py
     chmod +x ./graph_vibrations.py
     ```

  5. Add this new section at the end of your `printer.cfg` file:
     ```
     [gcode_shell_command plot_graph]
     command: ~/printer_data/config/scripts/is_workflow/is_workflow.py
     timeout: 600.0
     verbose: True
     ```


## Usage

Be sure your machine is homed and then call one of the following macros:
  - `BELTS_SHAPER_CALIBRATION` to get the belt resonnance graphs. This is usefull to verify the belts tension, but also to check if the belt paths are OK.
  - `AXES_SHAPER_CALIBRATION` to get the input shaper graphs and suppress the ringing/ghosting artefacts in your prints by setting correctly Klipper's [input_shaper] system.
  - `VIBRATIONS_CALIBRATION` to get the machine vibrations graphs and select the best speeds for your slicer profile.

Then, look for the results in the results folder. You can find them directly in your config folder by using the WebUI of Mainsail/Fluidd. You can get some hints on the results in my documentation about how to [read and interpret the IS graphs](../input_shaper.md).
