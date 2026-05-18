from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.core import callback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the scavenger hunt binary sensors."""
    manager = hass.data[DOMAIN]
    
    entities = [ScavengerHuntCompletionSensor(manager)]
    
    # Add an entity for each tag
    for tag_id, tag_config in manager.tags_config.items():
        entities.append(ScavengerHuntTagSensor(manager, tag_id, tag_config["name"]))
        
    async_add_entities(entities)

class ScavengerHuntCompletionSensor(BinarySensorEntity):
    """Sensor tracking if the hunt is complete."""

    def __init__(self, manager):
        self._manager = manager
        self._attr_name = "Scavenger Hunt Completion"
        self._attr_unique_id = f"{DOMAIN}_completion"
        self._attr_is_on = False
        self._attr_icon = "mdi:check-decagram"

    async def async_added_to_hass(self):
        """Register update callback."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._update_state
            )
        )

    @callback
    def _update_state(self):
        """Update the sensor state."""
        self._attr_is_on = self._manager.game_completed
        self.async_write_ha_state()

class ScavengerHuntTagSensor(RestoreEntity, BinarySensorEntity):
    """Sensor tracking if a specific tag has been scanned."""

    def __init__(self, manager, tag_id, name):
        self._manager = manager
        self._tag_id = tag_id
        self._attr_name = f"Tag: {name}"
        self._attr_unique_id = f"{DOMAIN}_tag_{tag_id.replace(':', '_')}"
        self._attr_is_on = False
        self._attr_icon = "mdi:nfc-variant"

    async def async_added_to_hass(self):
        """Restore state and register update callback."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.state == "on":
            self._attr_is_on = True
            # Update the manager's set of scanned tags on startup
            self._manager.scanned_tags.add(self._tag_id)

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._update_state
            )
        )

    @callback
    def _update_state(self):
        """Update the sensor state."""
        self._attr_is_on = self._tag_id in self._manager.scanned_tags
        self.async_write_ha_state()
