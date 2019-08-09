# Custom components for Home Assistant
## Xiaomi IR Climate Component

Moved to [personal repository](https://github.com/Anonym-tsk/homeassistant-climate-xiaomi-remote) with [HACS](https://github.com/custom-components/hacs) support.

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
On linux (including Raspberry Pi) and [official docker container](https://hub.docker.com/r/homeassistant/home-assistant/) you can install it from `apt`:
```
sudo apt-get install libusb-1.0-0-dev
```

#### Example:
```
sensor:
  - platform: co2mon
```
