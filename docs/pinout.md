# Board pins details

This config extensively use `[board_pins]` sections to simplify the hardware configuration. In Klipper, once a `[board_pins]` is defined, then the pin `aliases` can be used in all the hardware sections to make them more readable. If you want to get more info about it, have a look [here in the official Klipper documentation](https://www.klipper3d.org/Config_Reference.html#board_pins)).

In the design process of this generic config, some rules and naming convention were defined and used in every preconfigured board_pins files for all the most used MCUs of the market. Then these aliases where used everywhere in this config.

  > **NOTA** : `[board_pins]` sections can not contain pin modifiers like `!`, `^` and `~`. Moreover, when multiple MCUs are configured at the same time, all the aliases used in the hardware sections have to be prefixed with the MCU name. This is a current limitation of Klipper that is limiting the "genericity" of this config: so please be sure to check all the harware section and pin definitions in all the file that you want to include in your config.

All the predefined board_pins files can be found in [config/mcus](../config/mcus). You can always adjust them to your needs.


## Aliases used in this config

#### Steppers
  - `[XYZ1-3E]_STEP`: drivers step pins
  - `[XYZ1-3E]_DIR`: drivers dir pins
  - `[XYZ1-3E]_ENABLE`: drivers enable pins
  - `[XYZ1-3E]_TMCUART`: drivers UART pins

#### Endstops & Probe
  - `[XYZ]_STOP`: classic axis endstops pins
  - `PROBE_INPUT`: probe pin

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
  - `FILTER_FAN`: pin for the recirculating filter (such as a Nevermore filter). This pin should be a PWM capable pin to allow power modulation
  - `CONTROLLER_FAN`: pin the fans that add airflow on your MCUs

#### Lights
  - `LIGHT_OUTPUT`: simple chamber lights (such as 24v leds or 24v fcob light bars)
  - `LIGHT_NEOPIXEL` : neopixel chamber lights
  - `STATUS_NEOPIXEL` : toolhead Neopixel lights (such as the one used on the Voron StealthBurner toolhead)

#### Other I/Os
  - `RUNOUT_SENSOR`: filament motion sensor pin
  - `TOOLHEAD_SENSOR`: filament motion sensor pin optional for ERCF
  - `SERVO_PIN`: servo pin for a mechanical and movable probe dock (such as the ones that are commonly found on the Voron V0 mods)


## Predefined pinouts

#### BTT Octopus

![octopus_pinout](./images/octopus_pinout.png)

#### Dual SKR 1.4

![skr_1.4_x2 pinout](./images/skr_1.4_x2_pinout.png)

#### Spider V1
#### Spider V2
#### Spider V1 + sht42
#### probably more to come ...


## External references

For more information on the boards and pinouts, please see directly the manufacturers website or github:
  - [BTT SKR 1.4](https://github.com/bigtreetech/BIGTREETECH-SKR-V1.3/tree/master/BTT%20SKR%20V1.4)
  - [BTT Octopus](https://github.com/bigtreetech/BIGTREETECH-OCTOPUS-V1.0)
  - [BTT Manta 8P](https://github.com/bigtreetech/Manta-M8P)
  - [Fystec Spiders](https://github.com/FYSETC/FYSETC-SPIDER)
  - [Fly SHT](https://mellow.klipper.cn/#/board/fly_sht36_42/)
  - [BTT EBB](https://github.com/bigtreetech/EBB)
