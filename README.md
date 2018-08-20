# Custom components for Home Assistant
## Xiaomi IR Climate Component

#### Requirements
[Xiaomi IR Remote](https://www.home-assistant.io/components/remote.xiaomi_miio/) component need to be enabled and configured

#### Configuration variables:
| Variable |  Required  | Description |
| -------- | ---------- | ----------- |
| `remote` | yes | **entity_id** of the Xiaomi IR Remote device |
| `commands` | yes | Commands list (see below) |
| `name` | no | Name of climate component |
| `temp_sensor` | no | **entity_id** for a temperature sensor, **temp_sensor.state must be temperature** |
| `power_template` | no | **template** that returns status of climete, **must returns boolean value** |
| `min_temp` | no | Set minimum available temperature (default: 16) |
| `max_temp` | no | Set maximum available temperature (default: 32) |
| `target_temp` | no | Set initial target temperature (default: 24) |
| `target_temp_step` | no | Set target temperature step (default: 1) |
| `operation_mode` | no | Set initial default operation mode (default: cool) |
| `fan_mode` | no | Set initial default fan mode (default: auto) |
| `customize`<br/>`- operation_list`<br/>`- fan_list` | no | List of options to customize<br/>- List of operation modes (default: heat, cool, auto)<br/>- List of fan modes (default: low, medium, high, auto) |

#### Basic Example:
```
climate:
  - platform: xiaomi_remote
    name: Air Conditioner
    remote: remote.xiaomi_miio_192_168_10_101
    commands: !include Roda-YKR-H-102E.yaml
```

#### Custom Example:
```
climate:
  - platform: xiaomi_remote
    name: Air Conditioner
    remote: remote.xiaomi_miio_192_168_10_101
    commands: !include Roda-YKR-H-102E.yaml
    temp_sensor: sensor.co2mon_temperature
    power_template: "{{ states('sensor.plug_power_158d0002366887') | float > 50 }}"
    min_temp: 16
    max_temp: 32
    target_temp: 24
    target_temp_step: 1
    operation_mode: cool
    fan_mode: auto
    customize:
      operation_list:
        - cool
        - heat
        - dry
        - fan_only
        - auto
      fan_list:
        - low
        - medium
        - high
        - auto
```

#### How to make your configuration YAML file
* Use [`remote.xiaomi_miio_learn_command`](https://www.home-assistant.io/components/remote.xiaomi_miio/#remotexiaomi_miio_learn_command) to get commands from your remote.
* Create YAML file same as `Roda-YKR-H-102E.yaml` with your commands.
  * Required command `off` (`'off': <command>`)
  * Optional command `idle` (`idle: <command>`)
  * Other commands: `operation/fan_mode/temperature` (available nesting: `operation/fan_mode/temperature`, `operation/fan_mode`, `operation`)
  * `'off'` commands must be in quotes

Example:
```
'off': <raw_command>
idle: <raw_command>
cool:
  low:
    16: <raw_command>
    17: <raw_command>
    ...
heat:
  low: <raw_command>
  high: <raw_command>
dry: <raw_command>
```

## Xiaomi Plug Power Sensor

Component provides sensors with current power of Xiaomi Plugs. Also, component fixes long updates of `in_use` and `load_power` attributes of plug (default update interval is [5-8 minutes](http://docs.opencloud.aqara.cn/en/guideline/product-discription/#smart-plug))

#### Example:
```
sensor:
  - platform: xiaomi_plug_power
```


## CO2Mon Sensor

Component provides two sensors - temperature and CO2 from [USB CO2 monitor](https://habr.com/company/masterkit/blog/248403/)

#### Requirements
The `libusb` library must be installed.<br/>
On linux (including Raspberry Pi) you can install it from `apt`:
```
sudo apt-get install libusb-1.0-0-dev
```
It already installed in [official docker container](https://hub.docker.com/r/homeassistant/home-assistant/)

#### Example:
```
sensor:
  - platform: co2mon
```
