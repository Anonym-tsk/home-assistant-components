import logging

from homeassistant.helpers.entity import Entity
from homeassistant.components.xiaomi_aqara import PY_XIAOMI_GATEWAY

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    devices = []

    for (_, gateway) in hass.data[PY_XIAOMI_GATEWAY].gateways.items():
        for device in gateway.devices['switch']:
            if device['model'] == 'plug':
                devices.append(XiaomiPowerSensor(gateway, device))

    add_devices(devices)


class XiaomiPowerSensor(Entity):
    def __init__(self, gateway, device):
        self._gw = gateway
        self._sid = device['sid']
        self._state = None

        gateway.callbacks[self._sid].append(self._parse_data)
        self._parse_data(device['data'], device['raw_data'])

    def _parse_data(self, data, raw_data):
        if 'load_power' in data:
            self._state = round(float(data['load_power']), 2)

        if 'inuse' in data:
            inuse = int(data['inuse'])
            if not inuse:
                self._state = 0

    @property
    def name(self):
        return 'Plug Power ' + self._sid

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return 'W'

    def update(self):
        self._gw.get_from_hub(self._sid)
