# Klippain

> Klippain - the pain-free recipe for (french)bread and butter Klipper configuration!

![Klippain](./docs/klippain.png)

Klippain is a generic and modular Klipper configuration for CoreXY 3D printers. I use it on my Voron V2.4 (V2.1237), my Voron Trident, my custom TriZero, and my heavily modified Prusa i3 MK3s. Other CoreXY printer owners (Voron, VZbot, Ender5, ...) have also reported no issues using it.

The files are frequently updated with new features that I create, but also with merged PRs from users. **Always** look, think, understand, and adjust to your own. But that should work in most cases. You can reach me in the Voron Discord: I'm **Frix_x#0161**.

Yes, "pain" \pɛ̃\ is the french word for bread: there is no pain in pain, only joy. Thanks to the french channel "honhonhonbaguette-FR" on the Voron Discord for this joke and name suggestion!


## Features

Klippain is designed to be generic: you can use it on a wide variety of machines by simply selecting and enabling the hardware and software options that you need.

The **adaptive bed mesh** functionality I wrote some time ago, the **custom calibration macros** for pressure advance & flow, the **automated input shaper workflows**, and the **vibrations measurement** macros and scripts are among the custom features available out of the box.

Here is a [list with the details and usage instruction for all the features](./docs/features.md). There are also some installation instructions in their documentation if you want to use them standalone in your own personal configuration.


## Installation

Installing Klippain should not be too complicated if you are already familiar with the Klipper ecosystem. Make sure you already have Klipper, Moonraker, and a WebUI is installed on your printer. You can use [KIAUH](https://github.com/th33xitus/kiauh) if you don't.

Then, to run the installation script, connect to your printer using SSH and type the following command:
```
wget -O - https://raw.githubusercontent.com/Frix-x/klippain/main/install.sh | bash
```
  
This script will backup your old configuration, download this GitHub repository into your RaspberryPi home directory and setup the entire environment in `~/printer_data/config`. You'll also be asked if you want to select and install some MCU board_pins templates. This is recommended as it will allow a very fast filling of your `mcu.cfg` user file, but you can always do it manually afterwards if you prefer.


## Configuration

To configure and customize everything for your printer, there are some additional steps required. Please follow them carefully!

#### 1. MCUs settings
If you didn't install any MCU templates during the installation (or want to customize the default wiring), you will need to modify your `mcu.cfg` file by following the [MCU pinout and wiring documentation](./docs/pinout.md).

Also, do not forget to fill in the serial_port or can_uuid of your MCUs. If needed, you can refer to the [official klipper documentation](https://www.klipper3d.org/FAQ.html#wheres-my-serial-port) to find them.

#### 2. Printer settings, overrides and variables
Open the `printer.cfg` file and uncomment the lines that correspond to your printer hardware or software components in order to enable them (such as extruder type, XY motors, Z motors, QGL vs Z_TILT, etc...). This will customize the behavior of this generic Klipper configuration and will also enable the corresponding macros.

Then it's time to customize the configuration by editing the `overrides.cfg` user file by following the [overrides documentation and examples](./docs/overrides.md). You can tweak the machine dimensions, limits, currents, and everything else in all this config sections. You can also use the overrides to invert motor directions, etc...

When Klipper is able to boot, modify and adapt the `variables.cfg` file to suit the configuration of your machine. This file adds additional customization to how all the macros will behave (coordinates of everything, enable/disable some software features, etc...).

#### 3. Initial startup of the machine
Before printing for the first time, you will need to **check all the features very carefully to avoid any problems on your machine!** You can start by following the [config checks section from the official Klipper documentation](https://www.klipper3d.org/Config_checks.html).
Then, also check that you are able to attach/detach the mechanical probe (if you use one), do a QGL/Z_TILT, have correct coordinates for all the used components (purge bucket, physical Z endstop, etc...). You should also check your first layer calibration (and the `switch_offset` parameter of the automatic z calibration plugin if you use it), etc...

Finally when everything seems to work, you need to add the custom print start gcode to your slicer. Here is an example for SuperSlicer:     
```
START_PRINT EXTRUDER_TEMP={first_layer_temperature[initial_extruder] + extruder_temperature_offset[initial_extruder]} BED_TEMP=[first_layer_bed_temperature] MATERIAL=[filament_type] CHAMBER=[chamber_temperature] SIZE={first_layer_print_min[0]}_{first_layer_print_min[1]}_{first_layer_print_max[0]}_{first_layer_print_max[1]}
```

Also add the custom print end gcode to your slicer:

```
END_PRINT
```


## Sponsor the work

I try to be open to any user request if it fits into this configuration design. So feel free to open an issue or a PR if you want your specific hardware device or new feature to be supported.

Alternatively, you can also buy me a coffee or help me buy new hardware to support my work :)
