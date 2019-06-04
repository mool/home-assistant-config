# BGH Smart componment

This integration will let you control your BGH Smart HVAC from Home Assistant.

## Installation

Copy this folder to `<config_dir>/custom_components/bgh_smart/`.

Add the following entry in your `configuration.yaml`:

```yaml
climate:
  - platform: bgh_smart
    username: USERNAME_HERE
    password: PASSWORD_HERE
```
