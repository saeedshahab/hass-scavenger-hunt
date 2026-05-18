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

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the scavenger hunt binary sensors from a config entry."""
    manager = hass.data[DOMAIN]
    
    # Clean up orphaned tag entities from the Entity Registry
    from homeassistant.helpers import entity_registry as er
    entity_registry = er.async_get(hass)
    
    registry_entries = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )
    
    configured_tag_unique_ids = {
        f"{DOMAIN}_tag_{tag_id.replace(':', '_')}" 
        for tag_id in manager.tags_config
    }
    
    for registry_entry in registry_entries:
        if (
            registry_entry.domain == "binary_sensor"
            and registry_entry.unique_id.startswith(f"{DOMAIN}_tag_")
            and registry_entry.unique_id not in configured_tag_unique_ids
        ):
            entity_registry.async_remove(registry_entry.entity_id)

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
