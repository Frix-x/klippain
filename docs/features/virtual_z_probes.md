# Virtual-Z Probe Framework

Klippain supports probes that act as the Z endstop through concrete probe profile includes. Users still select one probe include in `user_templates/printer.cfg`; the framework underneath standardizes contact temperature guarding, Z-home dispatch, and generic start-print actions.

## Probe Profiles

Use one probe include:

```ini
[include config/hardware/probes/voron_tap.cfg]
[include config/hardware/probes/beacon_contact.cfg]
[include config/hardware/probes/cartographer_touch.cfg]
```

`voron_tap.cfg` keeps the legacy internal identifier `probe_type_enabled: "vorontap"` for compatibility.

## Shared Contact Variables

Preferred variables:

```ini
variable_probe_contact_max_temp: 150
variable_probe_contact_deactivation_zhop: 5
variable_probe_unsupported_contact_action_policy: "warn"
```

Legacy variables remain supported for existing configs:

```ini
variable_tap_max_probing_temp: 150
variable_tap_deactivation_zhop: 5
variable_beacon_max_probing_temp: 150
variable_beacon_deactivation_zhop: 5
```

If both shared and legacy variables are set, the shared variable wins. With verbose output enabled, Klippain reports the override at startup.

## Start-Print Actions

Generic actions:

```ini
contact_z_home
contact_auto_calibrate
```

`contact_z_home` runs a probe-supported contact Z-home operation. `contact_auto_calibrate` runs a probe-supported contact model calibration, such as Beacon Contact autocalibration. Cartographer Survey Touch does not run `CARTOGRAPHER_TOUCH_CALIBRATE` during normal start print; that remains a user-initiated setup operation.

contact_z_home fails closed when the active probe profile does not support hook-based contact Z-home. contact_auto_calibrate warns and no-ops by default when unsupported, or raises when this policy is set to `error`:

```ini
variable_probe_unsupported_contact_action_policy: "error"
```

## Developer Notes

To add a new virtual-Z contact probe, create a concrete profile in `config/hardware/probes/`. Set capability variables and include a hook file only when the probe needs product-specific commands.

Valid operation modes:

- `none`
- `standard_g28`
- `hook`

Hook macros receive `SOURCE`, which is one of `homing`, `start_print`, or `manual`.

`standard_g28` is for Z-home dispatch. Auto-calibration support should use `hook` or `none`.
