from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DOMAIN, 
    ATTR_SCORE, 
    ATTR_TOTAL_TAGS, 
    ATTR_LAST_TAG, 
    ATTR_LIFELINES,
    SERVICE_GUESS_BYPASS,
    SERVICE_REVEAL_TOTAL,
    SERVICE_JUMP_THE_LINE
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the scavenger hunt sensor."""
    manager = hass.data[DOMAIN]
    async_add_entities([ScavengerHuntScoreSensor(manager)])

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the scavenger hunt sensor from a config entry."""
    manager = hass.data[DOMAIN]
    async_add_entities([ScavengerHuntScoreSensor(manager)])

class ScavengerHuntScoreSensor(RestoreEntity, SensorEntity):
    """Sensor tracking the scavenger hunt score."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Scavenger Hunt Score"
        self._attr_unique_id = f"{DOMAIN}_score"
        self._attr_native_value = 0
        self._attr_icon = "mdi:counter"

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            try:
                self._attr_native_value = int(state.state)
            except (ValueError, TypeError):
                self._attr_native_value = 0
        
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._update_state
            )
        )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        # Calculate lifelines for display
        lifelines = []
        score = len(self._manager.scanned_tags)
        total = self._manager.total_tags_count
        
        # Determine active lifelines
        req_met = not self._manager.required_tags or self._manager.required_tags.issubset(self._manager.scanned_tags)
        
        if score < (total - 2):
            if req_met and not self._manager.bypass_attempted:
                lifelines.append(SERVICE_GUESS_BYPASS)
        elif not self._manager.revealed_total:
            lifelines.append(SERVICE_REVEAL_TOTAL)
        elif score == (total - 1):
            lifelines.append(SERVICE_JUMP_THE_LINE)

        return {
            ATTR_TOTAL_TAGS: total,
            ATTR_LAST_TAG: self._manager.last_tag,
            ATTR_LIFELINES: lifelines,
            "revealed_total": self._manager.revealed_total,
            "tags_found": list(self._manager.scanned_tags),
            "last_verify_failed": self._manager.last_verify_failed,
            "last_sound_event": self._manager.last_sound_event
        }

    @callback
    def _update_state(self):
        """Update the sensor state."""
        self._attr_native_value = len(self._manager.scanned_tags)
        self.async_write_ha_state()
