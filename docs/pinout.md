# MCU pinout and wiring details

In Klipper, once a `[board_pins]` is defined, the aliases are used in all sections to make them more readable ([official board_pins Klipper documentation](https://www.klipper3d.org/Config_Reference.html#board_pins)). I use this mechanism extensively on a two-level model to add genericity and simplify the MCU configuration for everyone.


## Configuring your mcu.cfg file

Klippain is designed using a two-level [board_pins] model:
  1. First level: Some rules and pin naming conventions (let's call them "Frix-x names") were defined and used in all config files. Then a set of [user board_pins templates](./../user_templates/mcu_defaults/) were created for the most common MCUs of the market. This is basically what you need to put in your `mcu.cfg` file.
  2. Second level: Since it's always a pain to retrieve the pin names from the boards manufacturer's documentation like `PA12` or `gpio23` (let's call them "controller names"), I added a second layer of [board_pins] to link some "easy to retrieve names" (ie. what's printed on the MCU boards around the ports and easy to read with "MCU_" as a prefix) to these "controller names". This second layer of board_pins is located [in this folder](./../config/mcu_definitions/) and is not intended to be modified.

To summarize, we have two board_pins used for each MCU. One user board_pins and one manufacturer board_pins. They link the following:
```
Frix-x names -> Manufacturer (PCB print) names > controller names
```

So in order to populate your own `mcu.cfg` file, just copy one of the [user template](./../user_templates/mcu_defaults/) into it. Then feel free to change the wiring to your liking. For example, if you have wired your part fan to port `FAN3` instead of `FAN0`, just change the definition to `PART_FAN=MCU_FAN3` and that's it!

  > **Info**
  > Klipper does not allow `[board_pins]` sections to contain pin modifiers such as `!`, `^` and `~`. Moreover, when configuring multiple MCUs at the same time, all the aliases used in the hardware sections must be prefixed with the MCU name. This is a current limitation of Klipper and is why you need to use the overrides.cfg file to add them.


## Using a new MCU

If you want to use a new MCU that is not yet supported in my config, you just have to define a new [board_pins] in your `mcu.cfg` file and use the same convention. Also feel free to also add a manufacturer board_pins to my config and submit a PR: I'll be happy to merge it and extend MCU support for new boards :)

Here is a list of all the "Frix-x names" available to use in your own board_pins:

#### Steppers
  - `[EXYZ1-3]_STEP`: drivers step pins
  - `[EXYZ1-3]_DIR`: drivers dir pins
  - `[EXYZ1-3]_ENABLE`: drivers enable pins
  - `[EXYZ1-3]_TMCUART`: drivers UART pins
  - Beside standard axis there is also the support for the `GEAR_...` and `SELECTOR_...` drivers used in the ERCF

#### Endstops & Probe
  - `[XYZ]_STOP`: classic axis endstops pins
  - `PROBE_INPUT`: classical probe like Klicky, Omron, Pinda, TAP, etc...

#### Heaters    
  - `E_HEATER`: hotend heater cartridge
  - `BED_HEATER`: bed heating pad (or bed SSR)

#### Temperature sensors
  - `E_TEMPERATURE`: hotend temperature sensor
  - `BED_TEMPERATURE`: bed temperature sensor
  - `CHAMBER_TEMPERATURE`: chamber temperature sensor
  - `ELECTRICAL_CABINET_TEMPERATURE`: electrical cabinet temperature sensor (not really used in the config, but if present, this sensor is added to the Mainsail / Fluidd web interface as an additional info)

#### Fans
  - `E_FAN`: hotend fan. This fan should stay at 100% whenever the hotend is hot, so a PWM capable pin is not mandatory
  - `PART_FAN`: part fan used during the print. This pin should be a PWM capable pin to allow power modulation
  - `EXHAUST_FAN`: for an exhaust filter (such as the Voron basic exhaust). This pin should be a PWM capable pin to allow power modulation
  - `FILTER_FAN`: for a filter (such as a Nevermore filter). This pin should be a PWM capable pin to allow power modulation
  - `CONTROLLER_FAN`: to cool down your MCUs or electronic bay
  - `HOST_CONTROLLER_FAN`: to cool down your Pi (or equivalent Klipper host controller)

#### Lights
  - `LIGHT_OUTPUT`: simple chamber lights (such as 24v leds or 24v fcob light bars)
  - `LIGHT_NEOPIXEL` : neopixel chamber lights
  - `STATUS_NEOPIXEL` : toolhead neopixel lights (such as the one used on the Voron StealthBurner toolhead)

#### Other I/Os
  - `RUNOUT_SENSOR`: filament motion sensor
  - `ERCF_ENCODER`: filament motion sensor used in the ERCF carriage
  - `TOOLHEAD_SENSOR`: toolhead filament sensor used for the ERCF
  - `SERVO_PIN`: for a mechanical and movable probe dock or brush (such as the ones that are commonly found on the Voron V0 mods)
  - `ERCF_SERVO`: for a the ERCF servo


## External references

For more information on the boards and pinouts, please see directly the manufacturers website or github:
  - [BTT Octopus](https://github.com/bigtreetech/BIGTREETECH-OCTOPUS-V1.0)
  - [Fystec Spiders](https://github.com/FYSETC/FYSETC-SPIDER)
  - [BTT SKR 1.4](https://github.com/bigtreetech/BIGTREETECH-SKR-V1.3/tree/master/BTT%20SKR%20V1.4)
  - [BTT Manta 8P](https://github.com/bigtreetech/Manta-M8P)
  - [Fly SHT](https://mellow.klipper.cn/#/board/fly_sht36_42/)
  - [BTT EBB](https://github.com/bigtreetech/EBB)
