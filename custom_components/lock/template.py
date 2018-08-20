import asyncio
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.core import callback
from homeassistant.components.lock import (LockDevice, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME, CONF_OPTIMISTIC, CONF_VALUE_TEMPLATE, EVENT_HOMEASSISTANT_START)
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.script import Script

_LOGGER = logging.getLogger(__name__)

CONF_LOCK = 'lock'
CONF_UNLOCK = 'unlock'

DEFAULT_NAME = 'Template Lock'
DEFAULT_OPTIMISTIC = False

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_LOCK): cv.SCRIPT_SCHEMA,
    vol.Required(CONF_UNLOCK): cv.SCRIPT_SCHEMA,
    vol.Required(CONF_VALUE_TEMPLATE): cv.template,
    vol.Optional(CONF_OPTIMISTIC, default=DEFAULT_OPTIMISTIC): cv.boolean
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    value_template = config.get(CONF_VALUE_TEMPLATE)
    value_template.hass = hass

    async_add_devices([TemplateLock(
        hass,
        config.get(CONF_NAME),
        config.get(CONF_VALUE_TEMPLATE),
        config.get(CONF_LOCK),
        config.get(CONF_UNLOCK),
        config.get(CONF_OPTIMISTIC)
    )])


class TemplateLock(LockDevice):
    def __init__(self, hass, name, value_template, command_lock, command_unlock, optimistic):
        self._state = False
        self._hass = hass
        self._name = name
        self._state_template = value_template
        self._state_entities = value_template.extract_entities()
        self._command_lock = Script(hass, command_lock)
        self._command_unlock = Script(hass, command_unlock)
        self._optimistic = optimistic

    @asyncio.coroutine
    def async_added_to_hass(self):
        @callback
        def template_lock_state_listener(entity, old_state, new_state):
            self.async_schedule_update_ha_state(True)

        @callback
        def template_lock_startup(event):
            async_track_state_change(self.hass, self._state_entities, template_lock_state_listener)
            self.async_schedule_update_ha_state(True)

        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, template_lock_startup)

    @property
    def assumed_state(self):
        return self._optimistic

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def is_locked(self):
        return self._state

    @asyncio.coroutine
    def async_lock(self, **kwargs):
        if self._optimistic:
            self._state = True
            self.async_schedule_update_ha_state()
        yield from self._command_lock.async_run()

    @asyncio.coroutine
    def async_unlock(self, **kwargs):
        if self._optimistic:
            self._state = False
            self.async_schedule_update_ha_state()
        yield from self._command_unlock.async_run()
