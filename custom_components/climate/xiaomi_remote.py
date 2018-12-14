import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.climate import (
    ClimateDevice, PLATFORM_SCHEMA,
    STATE_OFF, STATE_HEAT, STATE_COOL, STATE_AUTO, STATE_UNKNOWN,
    ATTR_OPERATION_MODE, ATTR_OPERATION_LIST, ATTR_MAX_TEMP, ATTR_MIN_TEMP,
    ATTR_TARGET_TEMP_STEP, ATTR_FAN_MODE, ATTR_FAN_LIST, SUPPORT_ON_OFF,
    SUPPORT_OPERATION_MODE, SUPPORT_TARGET_TEMPERATURE, SUPPORT_FAN_MODE)
from homeassistant.components.fan import (
    SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH)
from homeassistant.components.remote import (
    ATTR_COMMAND, DOMAIN, SERVICE_SEND_COMMAND)
from homeassistant.const import (
    ATTR_TEMPERATURE, ATTR_ENTITY_ID, CONF_NAME, CONF_CUSTOMIZE)
from homeassistant.core import callback
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.restore_state import RestoreEntity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['remote']

CONF_REMOTE = 'remote'
CONF_TEMP_SENSOR = 'temp_sensor'
CONF_POWER_TEMPLATE = 'power_template'
CONF_TARGET_TEMP = 'target_temp'
CONF_COMMANDS = 'commands'

DEFAULT_NAME = 'Xiaomi Remote Climate'
DEFAULT_MIN_TEMP = 16
DEFAULT_MAX_TEMP = 32
DEFAULT_TARGET_TEMP = 24
DEFAULT_TARGET_TEMP_STEP = 1
DEFAULT_OPERATION_LIST = [STATE_OFF, STATE_HEAT, STATE_COOL, STATE_AUTO]
DEFAULT_FAN_MODE_LIST = [SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH, STATE_AUTO]
DEFAULT_OPERATION = STATE_COOL
DEFAULT_FAN_MODE = STATE_AUTO

ATTR_LAST_OPERATION = 'last_operation'
ATTR_LAST_FAN_MODE = 'last_fan_mode'
ATTR_SUPPORTED_FEATURES = 'supported_features'

COMMAND_POWER_OFF = 'off'

CUSTOMIZE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_OPERATION_LIST): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_FAN_LIST): vol.All(cv.ensure_list, [cv.string])
})

COMMANDS_SCHEMA = vol.Schema({
    vol.Required(COMMAND_POWER_OFF): cv.string
}, extra=vol.ALLOW_EXTRA)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_REMOTE): cv.entity_id,
    vol.Optional(CONF_TEMP_SENSOR): cv.entity_id,
    vol.Optional(CONF_POWER_TEMPLATE): cv.template,
    vol.Optional(ATTR_MIN_TEMP, default=DEFAULT_MIN_TEMP): cv.positive_int,
    vol.Optional(ATTR_MAX_TEMP, default=DEFAULT_MAX_TEMP): cv.positive_int,
    vol.Optional(CONF_TARGET_TEMP, default=DEFAULT_TARGET_TEMP): cv.positive_int,
    vol.Optional(ATTR_TARGET_TEMP_STEP, default=DEFAULT_TARGET_TEMP_STEP): cv.positive_int,
    vol.Optional(ATTR_OPERATION_MODE, default=DEFAULT_OPERATION): cv.string,
    vol.Optional(ATTR_FAN_MODE, default=DEFAULT_FAN_MODE): cv.string,
    vol.Optional(CONF_CUSTOMIZE, default={}): CUSTOMIZE_SCHEMA,
    vol.Required(CONF_COMMANDS): COMMANDS_SCHEMA
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the xiaomi remote climate platform."""
    name = config.get(CONF_NAME)
    remote_entity_id = config.get(CONF_REMOTE)
    commands = config.get(CONF_COMMANDS)

    min_temp = config.get(ATTR_MIN_TEMP)
    max_temp = config.get(ATTR_MAX_TEMP)
    target_temp = config.get(CONF_TARGET_TEMP)
    target_temp_step = config.get(ATTR_TARGET_TEMP_STEP)
    operation_list = config.get(CONF_CUSTOMIZE).get(ATTR_OPERATION_LIST, []) or DEFAULT_OPERATION_LIST
    fan_list = config.get(CONF_CUSTOMIZE).get(ATTR_FAN_LIST, []) or DEFAULT_FAN_MODE_LIST
    default_operation = config.get(ATTR_OPERATION_MODE)
    default_fan_mode = config.get(ATTR_FAN_MODE)

    temp_entity_id = config.get(CONF_TEMP_SENSOR)
    power_template = config.get(CONF_POWER_TEMPLATE)

    async_add_entities([
        RemoteClimate(hass, name, remote_entity_id, commands, min_temp, max_temp, target_temp, target_temp_step,
                      operation_list, fan_list, default_operation, default_fan_mode, temp_entity_id, power_template)
    ])


class RemoteClimate(ClimateDevice, RestoreEntity):
    def __init__(self, hass, name, remote_entity_id, commands, min_temp, max_temp, target_temp, target_temp_step,
                 operation_list, fan_list, default_operation, default_fan_mode, temp_entity_id, power_template):
        """Representation of a Xiaomi Remote Climate device."""

        self.hass = hass
        self._name = name
        self._remote_entity_id = remote_entity_id
        self._commands = commands

        self._min_temp = min_temp
        self._max_temp = max_temp
        self._target_temperature = target_temp
        self._target_temperature_step = target_temp_step
        self._unit_of_measurement = hass.config.units.temperature_unit

        self._current_temperature = None
        self._default_operation = default_operation
        self._current_operation = default_operation
        self._last_operation = default_operation
        self._default_fan_mode = default_fan_mode
        self._current_fan_mode = default_fan_mode
        self._last_fan_mode = default_fan_mode

        self._temp_entity_id = temp_entity_id
        self._power_template = power_template

        self._operation_list = operation_list
        self._fan_list = fan_list

        self._support_flags = SUPPORT_ON_OFF | SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE | SUPPORT_FAN_MODE
        self._enabled_flags = self._support_flags

        if temp_entity_id:
            async_track_state_change(hass, temp_entity_id, self._async_temp_changed)

        if power_template:
            power_template.hass = hass
            power_entity_ids = power_template.extract_entities()
            async_track_state_change(hass, power_entity_ids, self._async_power_changed)

    async def _async_temp_changed(self, entity_id, old_state, new_state):
        """Update current temperature."""
        if new_state is None:
            return

        self._async_update_temp(new_state)
        await self.async_update_ha_state()

    @callback
    def _async_update_temp(self, state):
        """Update temperature with latest state from sensor."""
        try:
            self._current_temperature = float(state.state)
        except ValueError as ex:
            _LOGGER.error("Unable to update from sensor: %s", ex)

    async def _async_power_changed(self, entity_id, old_state, new_state):
        """Update current power."""
        if new_state is None:
            return

        self._async_update_power()
        await self.async_update_ha_state()

    @callback
    def _async_update_power(self):
        """Update power with latest state from template."""
        try:
            if self._power_template.async_render().lower() not in ('true', 'on', '1'):
                self._current_operation = STATE_OFF
            else:
                self._current_operation = self._last_operation
        except TemplateError as ex:
            _LOGGER.warning('Unable to update power from template: %s', ex)

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """Return the sensor temperature."""
        return self._current_temperature

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._max_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._target_temperature_step

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool."""
        return self._current_operation

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        return self._current_fan_mode

    @property
    def fan_list(self):
        """Return the list of available fan modes."""
        return self._fan_list

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data = super().state_attributes
        data[ATTR_LAST_OPERATION] = self._last_operation
        data[ATTR_LAST_FAN_MODE] = self._last_fan_mode
        return data

    @property
    def is_on(self):
        """Return true if on."""
        return self._current_operation != STATE_OFF

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._enabled_flags

    def _update_flags_get_command(self):
        """Update supported features list."""
        if not self.is_on:
            command = self._commands[COMMAND_POWER_OFF]
        else:
            operation = self._current_operation.lower()
            fan_mode = self._current_fan_mode.lower()
            temp = int(self._target_temperature)

            try:
                if isinstance(self._commands[operation], str):
                    command = self._commands[operation]
                    self._enabled_flags = self._support_flags ^ SUPPORT_TARGET_TEMPERATURE ^ SUPPORT_FAN_MODE
                elif isinstance(self._commands[operation][fan_mode], str):
                    command = self._commands[operation][fan_mode]
                    self._enabled_flags = self._support_flags ^ SUPPORT_TARGET_TEMPERATURE
                else:
                    command = self._commands[operation][fan_mode][temp]
                    self._enabled_flags = self._support_flags
            except KeyError:
                command = None
                _LOGGER.error('Could not find command for %s/%s/%s', operation, fan_mode, temp)

        return command

    def _send_command(self):
        """Send IR code to device."""
        command = self._update_flags_get_command()
        if command is not None:
            self.hass.services.call(DOMAIN, SERVICE_SEND_COMMAND, {
                ATTR_COMMAND: 'raw:' + command,
                ATTR_ENTITY_ID: self._remote_entity_id
            })

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
            if self.is_on:
                self._send_command()
            self.schedule_update_ha_state()

    def set_fan_mode(self, fan):
        """Set new target fan mode."""
        self._current_fan_mode = fan
        self._last_fan_mode = fan
        if self.is_on:
            self._send_command()
        self.schedule_update_ha_state()

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        self._current_operation = operation_mode
        if operation_mode != STATE_OFF:
            self._last_operation = operation_mode
        self._send_command()
        self.schedule_update_ha_state()

    def turn_on(self):
        """Turn device on."""
        self.set_operation_mode(self._last_operation)

    def turn_off(self):
        """Turn device off."""
        self.set_operation_mode(STATE_OFF)

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()

        if state is not None:
            self._last_operation = state.attributes.get(ATTR_LAST_OPERATION, self._default_operation)
            self._current_operation = state.attributes.get(ATTR_LAST_OPERATION, self._last_operation)
            self._last_fan_mode = state.attributes.get(ATTR_LAST_FAN_MODE, self._default_fan_mode)
            self._current_fan_mode = state.attributes.get(ATTR_FAN_MODE, self._last_fan_mode)
            self._target_temperature = state.attributes.get(ATTR_TEMPERATURE, self._target_temperature)
            self._enabled_flags = state.attributes.get(ATTR_SUPPORTED_FEATURES, self._enabled_flags)

        if self._temp_entity_id:
            temp_state = self.hass.states.get(self._temp_entity_id)
            if temp_state and temp_state.state != STATE_UNKNOWN:
                self._async_update_temp(temp_state)

        if self._power_template:
            self._async_update_power()

        self._update_flags_get_command()
        await self.async_update_ha_state(True)
