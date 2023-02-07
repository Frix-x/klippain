# Generic Klipper configuration

This generic Klipper configuration is designed for CoreXY printers. I use it on my Voron V2.4 (V2.1237), my Voron Trident, my custom TriZero, and my heavily modified Prusa i3 MK3s. Other printer owners (on Voron, VZbot, Ender5, ...) have also reported no issues using it.

This is a WIP: the files are frequently updated with new features that I create, but also with merged PRs from users. **Always** look, think, understand, and adjust to your own. But that should work in most cases. You can reach me in the Voron Discord: I'm **Frix_x#0161**.


## Features

This configuration is designed to be generic: you can use it on a wide variety of machines by simply selecting and enabling the hardware and software options that you need.

The **adaptive bed mesh** functionality I wrote some time ago, the **custom calibration macros** for pressure advance & flow, the **automated input shaper workflows**, and the **vibrations measurement** macros and scripts are among the custom features available out of the box.

Here is a [list with the details and usage instruction for all the features](./docs/features.md). There are also some installation instructions in their documentation if you want to use them standalone in your own personal configuration.


## Installation

Installing this config folder should not be too complicated if you are already familiar with the Klipper ecosystem. Here is how:
  1. Use an SSH connection to connect to your printer and type the following command to run the install script. This should backup your old configuration, then download and replace it by my configuration and finally set up the environment for you.

     ```
     wget -O - https://raw.githubusercontent.com/Frix-x/klipper-voron-V2/main/install.sh | bash
     ```
  
  3. TODO: write how to setup the printer.cfg, wiring.cfg, overrides.cfg, ...


## Sponsor the work

I try to be open to any user request if it fits into this configuration design. So feel free to open an issue or a PR if you want your specific hardware device or new feature to be supported.

Alternatively, you can also buy me a coffee or help me buy new hardware to support my work :)
