"""BGH Smart integration."""

import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.climate import ClimateDevice, PLATFORM_SCHEMA

from homeassistant.components.climate.const import (
    SUPPORT_TARGET_TEMPERATURE, SUPPORT_OPERATION_MODE,
    SUPPORT_FAN_MODE,
    SUPPORT_ON_OFF,
    STATE_HEAT, STATE_COOL, STATE_FAN_ONLY, STATE_DRY, STATE_AUTO)
from homeassistant.const import (
    ATTR_ENTITY_ID, ATTR_STATE, ATTR_TEMPERATURE,
    CONF_USERNAME, CONF_PASSWORD,
    STATE_ON, STATE_OFF, STATE_UNKNOWN, TEMP_CELSIUS, TEMP_FAHRENHEIT)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string
})

FAN_AUTO = 'auto'
FAN_LOW = 'low'
FAN_MEDIUM = 'medium'
FAN_HIGH = 'high'

MAP_MODE_ID = {
    0: STATE_OFF,
    1: STATE_COOL,
    2: STATE_HEAT,
    3: STATE_DRY,
    4: STATE_FAN_ONLY,
    254: STATE_AUTO
}

MAP_FAN_MODE_ID = {
    1: FAN_LOW,
    2: FAN_MEDIUM,
    3: FAN_HIGH,
    254: FAN_AUTO
}

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the BGH Smart platform."""
    import pybgh

    # Assign configuration variables.
    # The configuration check takes care they are present.
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]

    # Setup connection with devices/cloud
    client = pybgh.BghClient(username, password)
    devices = []
    for home in client.get_homes():
        home_devices = client.get_devices(home['HomeID'])
        for _device_id, device in home_devices.items():
            devices.append(device)

    # Verify that passed in configuration works
    if not client.token:
        _LOGGER.error("Could not connect to BGH Smart cloud")
        return

    # Add devices
    add_entities(BghHVAC(device, client) for device in devices)

class BghHVAC(ClimateDevice):
    """Representation of a BGH Smart HVAC."""

    def __init__(self, device, client):
        """Initialize a BGH Smart HVAC."""
        self._device = device
        self._client = client

        self._device_name = self._device['device_name']
        self._device_id = self._device['device_id']
        self._home_id = self._device['device_data']['HomeID']
        self._min_temp = None
        self._max_temp = None
        self._current_temperature = None
        self._target_temperature = None
        self._mode = STATE_UNKNOWN
        self._power = False
        self._fan_speed = STATE_UNKNOWN

        self._parse_data()

        self._operation_list = [STATE_AUTO, STATE_COOL, STATE_HEAT, STATE_DRY,
                                STATE_FAN_ONLY, STATE_OFF]
        self._fan_list = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
        self._support = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE |
                         SUPPORT_FAN_MODE)

    def _parse_data(self):
        """Parse the data in self._device"""
        self._min_temp = 17
        self._max_temp = 30

        if self._device['raw_data']:
            self._current_temperature = self._device['data']['temperature']
            self._target_temperature = self._device['data']['target_temperature']
            self._mode = MAP_MODE_ID[self._device['data']['mode_id']]
            self._power = self._mode != 'off'
            self._fan_speed = MAP_FAN_MODE_ID[self._device['data']['fan_speed']]

    def update(self):
        """Fetch new state data for this HVAC.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._device = self._client.get_status(self._home_id, self._device_id)
        self._parse_data()

    @property
    def name(self):
        """Return the display name of this HVAC."""
        return self._device_name

    @property
    def temperature_unit(self):
        """BGH Smart API uses celsius on the backend."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return self._target_temperature

    @property
    def min_temp(self):
        """Return the minimum temperature for the current mode of operation."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature for the current mode of operation."""
        return self._max_temp

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support

    @property
    def current_operation(self):
        """Return the current mode of operation if unit is on."""
        if self._power:
            return self._mode
        return STATE_OFF

    @property
    def operation_list(self):
        """List of available operation modes."""
        return self._operation_list

    @property
    def is_on(self):
        """Return true if on."""
        return self._power

    @property
    def current_fan_mode(self):
        """Return whether the fan is on."""
        return self._fan_speed

    @property
    def fan_list(self):
        """List of available fan modes."""
        return self._fan_list

    ####### TO DO
    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        self._client.set_mode(self._device_id, self._mode, temperature, self._fan_speed)

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        self._mode = operation_mode
        if operation_mode == STATE_OFF:
            self._power = False
        else:
            self._power = True

        self._client.set_mode(self._device_id, operation_mode, self._target_temperature, self._fan_speed)

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        return true

    def turn_on(self):
        """Turn device on."""
        self._power = True
        self._client.set_mode(self._device_id, self._mode, self._target_temperature, self._fan_speed)

    def turn_off(self):
        """Turn device off."""
        self._power = False
        self._client.set_mode(self._device_id, STATE_OFF, self._target_temperature, self._fan_speed)
