"""Support for Efesto heating devices."""
import logging

from pyevacalor import (  # pylint: disable=redefined-builtin
    ConnectionError,
    Error as EvaCalorError,
    UnauthorizedError,
    evacalor,
)

from homeassistant.components.climate import ClimateDevice
from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_EMAIL,
    CONF_PASSWORD,
    PRECISION_WHOLE,
    TEMP_CELSIUS,
)

from .const import (
    ATTR_DEVICE_STATUS,
    ATTR_HUMAN_DEVICE_STATUS,
    ATTR_REAL_POWER,
    ATTR_SMOKE_TEMP,
    CONF_UUID,
    DOMAIN,
    FAN_1,
    FAN_2,
    FAN_3,
    FAN_4,
    FAN_5,
)

_LOGGER = logging.getLogger(__name__)

FAN_MODES = [
    FAN_1,
    FAN_2,
    FAN_3,
    FAN_4,
    FAN_5,
]

CURRENT_HVAC_MAP_EFESTO_HEAT = {
    "ON": CURRENT_HVAC_HEAT,
    "CLEANING FIRE-POT": CURRENT_HVAC_HEAT,
    "FLAME LIGHT": CURRENT_HVAC_HEAT,
    "OFF": CURRENT_HVAC_OFF,
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Eva Calor climate, nothing to do."""


async def async_setup_entry(hass, entry, async_add_entities):
    """Add Eva Calor device entry."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    gen_uuid = entry.data[CONF_UUID]

    try:
        eva = evacalor(email, password, gen_uuid)
        device = eva.devices[0]
    except UnauthorizedError:
        _LOGGER.error("Wrong credentials for Eva Calor")
        return False
    except ConnectionError:
        _LOGGER.error("Connection to Eva Calor not possible")
        return False
    except EvaCalorError as err:
        _LOGGER.error("Unknown Eva Calor error: %s", err)
        return False

    async_add_entities(
        [EvaCalorHeatingDevice(device)], True,
    )

    return True


class EvaCalorHeatingDevice(ClimateDevice):
    """Representation of an Eva Calor heating device."""

    def __init__(self, device):
        """Initialize the thermostat."""
        self.device = device
        self._device_id = device.id_device
        self._on = False
        self._device_status = None
        self._human_device_status = None
        self._current_temperature = None
        self._target_temperature = None
        self._smoke_temperature = None
        self._real_power = None
        self._current_power = None
        self._name = device.name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        return {
            ATTR_DEVICE_STATUS: self._device_status,
            ATTR_HUMAN_DEVICE_STATUS: self._human_device_status,
            ATTR_SMOKE_TEMP: self._smoke_temperature,
            ATTR_REAL_POWER: self._real_power,
        }

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._device_id

    @property
    def name(self):
        """Return the name of the Efesto, if any."""
        return self._name

    @property
    def device_info(self):
        """Return the device info."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Micronova",
            "model": self.device.name_product,
        }

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_WHOLE

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return PRECISION_WHOLE

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def min_temp(self):
        """Return the minimum temperature to set."""
        return self.device.min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature to set."""
        return self.device.max_temp

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.

        Need to be one of HVAC_MODE_*.
        """
        if self._on:
            return HVAC_MODE_HEAT
        return HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.

        Need to be a subset of HVAC_MODES.
        """
        return [HVAC_MODE_HEAT, HVAC_MODE_OFF]

    @property
    def fan_mode(self):
        """Return fan mode."""
        if self._current_power in FAN_MODES:
            return self._current_power
        return FAN_1

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return FAN_MODES

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.

        Need to be one of CURRENT_HVAC_*.
        """
        if self._human_device_status in CURRENT_HVAC_MAP_EFESTO_HEAT:
            return CURRENT_HVAC_MAP_EFESTO_HEAT.get(self._human_device_status)
        return CURRENT_HVAC_IDLE

    def turn_off(self):
        """Turn device off."""
        try:
            self.device.turn_off()
        except EvaCalorError as err:
            _LOGGER.error("Failed to turn off device (original message: %s)", err)

    def turn_on(self):
        """Turn device on."""
        try:
            self.device.turn_on()
        except EvaCalorError as err:
            _LOGGER.error("Failed to turn on device (original message: %s)", err)

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        try:
            self.device.set_air_temperature = temperature * 2
        except EvaCalorError as err:
            _LOGGER.error("Failed to set temperature (original message: %s)", err)

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        if fan_mode is None:
            return

        try:
            self.device.set_power = fan_mode
        except EvaCalorError as err:
            _LOGGER.error("Failed to set temperature (original message: %s)", err)

    def set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        if hvac_mode == HVAC_MODE_OFF:
            self.turn_off()
        elif hvac_mode == HVAC_MODE_HEAT:
            self.turn_on()

    def update(self):
        """Get the latest data."""
        try:
            self.device.update()
        except UnauthorizedError:
            _LOGGER.error("Wrong credentials for device %s", self._device_id)
            return False
        except ConnectionError:
            _LOGGER.error("Connection to %s not possible", self._device_id)
            return False
        except EvaCalorError as err:
            _LOGGER.error("Error: %s", err)
            return False

        self._device_status = self.device.status
        self._current_temperature = float(self.device.air_temperature)
        self._target_temperature = float(self.device.set_air_temperature) / 2
        self._human_device_status = self.device.status_translated
        self._smoke_temperature = float(self.device.gas_temperature)
        self._real_power = int(self.device.real_power)
        self._current_power = int(self.device.set_power)

        if self._device_status == 0:
            self._on = False
        else:
            self._on = True

        return True
