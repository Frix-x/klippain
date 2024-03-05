# Features

This config is designed to be generic. You can use it on a lot of machines by selecting and enabling the hardware options you need. This also activate automatically the associated macros and process under the hood.

On the other hand, if you don't want to use this full config folder, most of the specific macros and software features can also be installed as standalone in your own config folder.


## Software

I tried, when possible, to put all the print settings directly in the Klipper config. My utlimate goal is be to be able to use the same Gcode file (sliced generically) with multiple materials or even share it across multiple printers. That's why I use and set firmware retraction, set pressure advance in the macros, etc...

Here you can find a list of all the custom features availables in the macros or in the software configuration of this Klipper config:

  - [Adaptive bed mesh](./features/adaptive_bed_mesh.md) to mesh only where and when it's needed
  - Easy [pressure advance calibration](./features/pa_calibration.md) macro
  - Easy [flow calibration](./features/flow_calibration.md) macro
  - Automatic [input shaper workflow](./features/is_workflow.md) to calibrate it without using SSH
  - Custom designed [vibrations measurements and calibration workflow](./features/vibr_measurements.md) to be able to do an advanced calibration of the machine speed settings and optimize your global mechanical assembly
  - More feature descriptions and info will be added later...


## Hardware

This config support out of the box a lot of different machine hardware configurations.

Please see [How to write an override](./overrides.md#how-to-write-an-override) in docs/overrides.md for more information on customizing your configuration.

