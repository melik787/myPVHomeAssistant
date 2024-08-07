from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature, CONF_HOST, CONF_DEVICE
from homeassistant.helpers.event import async_track_time_interval
import logging

from .const import DOMAIN, DATA_COORDINATOR, DEFAULT_MAX_VALUE, DEFAULT_MIN_VALUE, DEFAULT_MODE, DEFAULT_STEP, WIFI_METER_NAME, MIN_TIME_BETWEEN_UPDATES
from .coordinator import MYPVDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up the WWBoost number entity."""
    device_name = entry.data[CONF_DEVICE]
    if device_name != WIFI_METER_NAME:
        coordinator: MYPVDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
        host = entry.data[CONF_HOST]
        async_add_entities([WWBoost(coordinator, host, entry.title)])

class WWBoost(CoordinatorEntity, NumberEntity):
    """Representation of the WWBoost number entity"""

    def __init__(self, coordinator, host, name):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_name = name
        self._host = host
        self._min_value = DEFAULT_MIN_VALUE
        self._max_value = DEFAULT_MAX_VALUE
        self._value = float(self.coordinator.data.get("setup", {}).get("ww1boost", 500)) / 10
        self._step = DEFAULT_STEP
        self._unit_of_measurement = UnitOfTemperature.CELSIUS
        self._mode = DEFAULT_MODE
        self.serial_number = self.coordinator.data.get("info", {}).get("sn", "unknown")
        self._model = self.coordinator.data.get("info", {}).get("device", "unknown")
        self._number = f"ww1boost_{self._host}"
        self._name = f"Hot Water Assurance {self._host}"

    @property
    def device_info(self):
        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, self.serial_number)},
            "name": self._device_name,
            "manufacturer": "my-PV",
            "model": self._model,
        }
    
    @property
    def unique_id(self):
        """Return unique id based on device serial and variable."""
        return "{} {}".format(self.serial_number, self._number)

    @property
    def name(self):
        """Return the display name of this entity."""
        return self._name

    @property
    def native_min_value(self):
        """Return the minimum value of this number."""
        return self._min_value

    @property
    def native_max_value(self):
        """Return the maximum value of this number."""
        return self._max_value

    @property
    def native_value(self):
        """Return the current value of this number."""
        return self._value
    
    @property
    def native_step(self):
        """Return the step size for this number."""
        return self._step
    
    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement for this number."""
        return self._unit_of_measurement
    
    @property
    def mode(self):
        """Return mode of this entity"""
        return self._mode

    async def async_added_to_hass(self):
        """Handle entity which will be added to hass."""
        await super().async_added_to_hass()
        async_track_time_interval(self.hass, self._async_poll, MIN_TIME_BETWEEN_UPDATES)

    async def _async_poll(self, now):
        """Poll for updates."""
        await self.coordinator.async_request_refresh()
        if self.coordinator.last_update_success:
            self._value = self.coordinator.data.get("setup", {}).get("ww1boost", 500) / 10
            self.async_write_ha_state()

    async def async_set_native_value(self, value: float):
        """Set a new value for this number."""
        if self._min_value <= value <= self._max_value:
            self._value = value
            await self.coordinator.async_refresh()
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"Value {value} is out of range [{self._min_value}, {self._max_value}]")