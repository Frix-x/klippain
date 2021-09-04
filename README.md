# Voron V2.1237 config

This is my actual config folder for my Voron v2.4 printer.

Please mind this is a WIP and the config files are beeing updated very frequently depending of the mods I add to the machine or just if I want to. **Do not** take it as a fully compliant config : think and adapt to your own machine.
I also try to put all possible setting and customizations in the Klipper config as my ultimate goal would be to use the same Gcode file (sliced generically) with multiple materials or even share it across multiple printers. That's why I'm using firmware retraction, and I set Pressure Advance, etc... in my config.

You can reach out in Voron Discord: i'm **Frix_x#0161**

## Mods and hardware changes

I ended up modifying lots of components on this machine:
- Removables doors with new hinges
- Voron v2.2 style panels clip
- Handles 2x on top and 2x at bottom sides (This beast is 30Kg...)
- LDO 1.8° on Z axis (4) & LDO 0.9° on X/Y axis (2)
- LGX extruder
- Klicky probe (instead of the inductive Z sensor) for bed leveling and final Z0 setting
- AB-BN-30 tool body with 5015 part cooling fan CFD optimized
- MGN12H single rail on X axis
- MGC5 spherical Z joints
- FCOB light bars on top
- X/Y endstop PCB
- Chamber and electrical cabinet temperature sensors
- Nevermore Duo v5 filter
- Purge bucket with scrub for quick nozzle cleaning
- Magnetic steel flex plate with PEI and quick align stand

## Specific features & config

Config is divided in two folders : one for the hardware declarations and the other for all the macros. In this folders I tried to cut everything in files to be able to find and modify everything easily.
I tried to push the speed a little bit now I now my machines limits.

#### Z calibration

I'm running the klipper Z calibration plugin to compute automaticaly a correct Z offset at each beginning of the print, even if I change the nozzle, the hotend, the toolhead, the PEI, etc... This thing is wonderfull !
This plugin let you call the ```[z_calibration]``` config section and add some system macros as ```Z_CALIBRATE```. It need to be installed manually on top of klipper. Updates are done by Moonraker/Fluidd as well.

#### Klicky probe

To be able to use the automatic Z calibration process, I replaced the inductive probe by a touch probe. A BLTouch could work but not a good idea in an enclosed atmosphere and the Klicky probe is the way to go : it's very cheap and very precise.
A lot of macros are needed for this one to work and it could be a little tricky at first. All the system macros that use the probe are overiden to be able to attach or dock the Klicky probe accordingly.

#### Purge bucket

There is a purge bucket at the back of the machine with a brush to purge and clean the nozzle tip just before calibrating the Z offset. This ensure repeatability and consistency in the measurements.

#### Nevermore and chamber heating

Under the bed is a Nevermore duo v5 recirculating active carbon filter. This filter the VOCs generated during printing but the dual 5015 fans also serves as a quick chamber heat distribution system during the pre-print phase.

#### Adaptive bed mesh

This part is a work in progress and not finalized: the goal is to mesh only if it's needed (no mesh if there is a single part in the center of the bed). If a mesh is needed, I also want it to be focalized only where the parts are located.

#### Pre-print phase

The macro ```PRINT_START``` is dedicated to prepare the machine to print:
1. First this macro manage the heatsoak of the bed when needed. If I put the bed at temperature manually before starting a print, the macro will take care of that and will not do the heatsoak.
2. Then, there is a chamber heating phase using the nevermore fans at full power. This phase is customizable: it follow the chamber temperature setting from the slicer and there is also a timeout if the temperature is not reached in time. This phase ensure the chamber of the machine is at a good temperature for critical material like ABS that is very prone to warping and layer adhesion problems.
3. When the bed and chamber are at temperature, the machine goes for a quad gantry leveling, a purge of the hotend/nozzle, cleaning of the nozzle tip and auto Z calibration.
4. Then the macro apply custom material parameters like PA, nevermore filtering, retraction settings, etc...
5. At the end a full bed mesh is recorded (this will change soon with the addaptive bed mesh) before starting the print
