import logging

from homeassistant.const import (TEMP_CELSIUS, DEVICE_CLASS_TEMPERATURE)
from homeassistant.helpers.entity import Entity

REQUIREMENTS = ['CO2meter==0.2.5']

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    device = Device()

    add_devices([
        TemperatureSensor(device),
        CO2Sensor(device)
    ], update_before_add=True)


class Device():
    def __init__(self):
        self._monitor = None
        self._temp = None
        self._co2 = None

    def get_temp(self):
        if self._monitor is None:
            try:
                from co2meter import CO2monitor
                self._monitor = CO2monitor()
            except OSError:
                _LOGGER.warn('Could not connect to CO2Monitor')
                return

        try:
            data = self._monitor.read_data()
            self._temp = round(data[2], 1)
            self._co2 = data[1]
        except OSError:
            self._monitor = None
            self._temp = None
            self._co2 = None

        return self._temp

    def get_co2(self):
        return self._co2


class TemperatureSensor(Entity):
    def __init__(self, device):
        self._state = None
        self._device = device

    @property
    def state(self):
        return self._state

    @property
    def name(self):
        return 'CO2Mon Temperature'

    @property
    def unit_of_measurement(self):
        return TEMP_CELSIUS

    @property
    def device_class(self):
        return DEVICE_CLASS_TEMPERATURE

    def update(self):
        self._state = self._device.get_temp()


class CO2Sensor(Entity):
    def __init__(self, device):
        self._state = None
        self._device = device

    @property
    def state(self):
        return self._state

    @property
    def name(self):
        return 'CO2Mon CO2'

    @property
    def unit_of_measurement(self):
        return 'ppm'

    def update(self):
        self._state = self._device.get_co2()
