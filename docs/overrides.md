# Overrides details

In Klipper, when two (but identical) `[section]` are defined, the last one in the include order will replace the previous one. In addition, any missing values will be filled in by the last entry. This mechanism is called an "override".

It allow me to set default values for each configuration section that you can include from the `printer.cfg` file. Then, if you want to change those values, you can add some overrides without having to change all the files in this repo. This has the advantage of keeping my repo read-only and compatible with Moonraker's update manager.

Using this mechanism, you will be able to tweak the machine dimensions, limits, currents, and everything else in all these configuration sections. You can also use the overrides to invert motor directions, or even add/replace a macro, etc... This is a very powerful feature!

  > **Note**
  > Klipper does not allow `[board_pins]` sections to contain pin modifiers such as `!`, `^` and `~`. Moreover, when configuring multiple MCUs at the same time, all the aliases used in the hardware sections must be prefixed with the MCU name. This is a current limitation of Klipper and is why you will also need to use the overrides.cfg file to add them.


## Common overrides

Since my defaults are designed to be as generic as possible, you will not need to add as many overrides. However, there are still some common things you should take a look at. For example, **pay special attention to the axis limits** in the `[stepper_...]` sections, run current, etc... Also check the thermistor types in `[extruder]` and `[heated_bed]`, ... If you are using a multi-MCU configuration, you will also need to override any section where there are pins connected to the secondary board to explicitly add it. Finally, you will need to use overrides if you want to change direction of motors or adding a pull-up/down (using `!`, `^` and `~`).

In addition, if you want to add a new macro or even replace an existing one to adapt it to your use case, you can always do it the same way!


## How to write an override

>**Warning**  
> put any changes in your own `overrides.cfg` user file and **never modify my config directly** as your changes will be deleted when the repo is updated!

Let's say you want to change the motor current for the X axis. You'll need to override the `[tmc2209 stepper_x]` section because that's where this current is defined.
To do this, simply add this to your `overrides.cfg` file:
```
[tmc2209 stepper_x]
run_current: ...
```

Similarly, if you want to invert the Z2 motor direction, override the `[stepper_z2]` section and add a `!` before the pin name:
```
[stepper_z2]
dir_pin: !mcu:Z2_DIR
```
