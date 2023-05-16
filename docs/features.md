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

This list is not necessarily complete.

### Printer types
  - CoreXY (e.g. Voron v2.4, Voron Trident, Voron v0)
  - CoreXZ (e.g. Voron Switchwire)
  - Cartesian

### Mainboards
  - BTT Octopus
  - BTT SKR E3 mini v2
  - BTT SKR E3 mini v3
  - BTT SKR Pico v1.0
  - BTT SKR v1.4
  - Fysetc Spider v1.x
  - Fysetc Spider v2.x
  - 

### Toolheads
Toolheads in this case mean boards with own MCUs
  - BTT EBB 42 v1.0
  - BTT EBB 42 v1.1
  - BTT EBB 42 v1.2
  - BTT SB2209 v1.0
  - BTT SB2240 v1.0
  - Mellow SB2040
  - Mellow SHT36 v2.x
  - Mellow SHT36-42 v1.x

### ERCF boards
  - ERCF Easy BRD by Tircown
  - Mellow fly ERCF
  - Fysetc ERCF ERB (burrows)

### Motor types
  - 1.8 degree
  - 0.9 degree

### TMC types
  - TMC2209 (all)
  - TMC2240 (extruder only)

### Probe types
  - Inductive
  - Dockable
  - "Voron Tap"

### Extruder types
  - Clockwork 1
  - Clockwork 2
  - Orbiter 2.0
  - LGX Lite
  - LGX Heavy
  - Galileo

### Displays types
  - Mini 12864 by BTT
  - Mini 12864 by Fysetc

### Additional hardware / mods
  - ERCF - Happy Hare
  - Purge Bucket (without servo)
  - Purge with servo
  - Nevermore Filter
  - Z autocalibrate 
  - Filament Motion Sensor
  - Case light (fcob)
  - Case light (neopixel)
