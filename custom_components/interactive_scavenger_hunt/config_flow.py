import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_LIGHTS,
    CONF_MEDIA_PLAYER,
    CONF_TAGS,
    CONF_TAG_ID,
    CONF_NAME,
    CONF_REQUIRED,
)

class InteractiveScavengerHuntConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Interactive Scavenger Hunt."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self.entry_data = {
            "title": "Interactive Scavenger Hunt",
            CONF_LIGHTS: [],
            CONF_MEDIA_PLAYER: None,
            CONF_TAGS: [],
        }

    def _get_registered_tags_options(self):
        """Get options for registered tags dropdown from Home Assistant's Tag registry."""
        options = []
        tag_store = self.hass.data.get("tag")
        if tag_store:
            from homeassistant.helpers import entity_registry as er
            entity_registry = er.async_get(self.hass)
            
            for item in tag_store.async_items():
                tag_id = item.get("id")
                if not tag_id:
                    continue
                name = f"Tag {tag_id}"
                entity_id = entity_registry.async_get_entity_id("tag", "tag", tag_id)
                if entity_id:
                    entity = entity_registry.async_get(entity_id)
                    if entity:
                        name = entity.name or entity.original_name or name
                options.append({"value": tag_id, "label": f"{name} ({tag_id})"})
        return options

    async def async_step_user(self, user_input=None):
        """Handle the initial config step."""
        if user_input is not None:
            self.entry_data["title"] = user_input.get("title", "Interactive Scavenger Hunt")
            self.entry_data[CONF_LIGHTS] = user_input.get(CONF_LIGHTS, [])
            self.entry_data[CONF_MEDIA_PLAYER] = user_input.get(CONF_MEDIA_PLAYER)
            return await self.async_step_manage_tags()

        data_schema = vol.Schema(
            {
                vol.Required("title", default=self.entry_data["title"]): str,
                vol.Optional(CONF_LIGHTS): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="light", multiple=True)
                ),
                vol.Optional(CONF_MEDIA_PLAYER): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="media_player", multiple=False)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_manage_tags(self, user_input=None):
        """Show the tag management menu."""
        return self.async_show_menu(
            step_id="manage_tags",
            menu_options=["add_tag", "remove_tag", "finish"]
        )

    async def async_step_add_tag(self, user_input=None):
        """Add a new tag to the configuration."""
        errors = {}
        if user_input is not None:
            tag_id = user_input.get(CONF_TAG_ID) or user_input.get("selected_tag")
            if not tag_id:
                errors["base"] = "missing_tag_id"
            else:
                self.entry_data[CONF_TAGS].append({
                    CONF_TAG_ID: tag_id,
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_REQUIRED: user_input.get(CONF_REQUIRED, False),
                })
                return await self.async_step_manage_tags()

        registered_tags = self._get_registered_tags_options()
        schema_dict = {}
        if registered_tags:
            schema_dict[vol.Optional("selected_tag")] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=registered_tags,
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            )
            schema_dict[vol.Optional(CONF_TAG_ID)] = str
        else:
            schema_dict[vol.Required(CONF_TAG_ID)] = str

        schema_dict[vol.Required(CONF_NAME)] = str
        schema_dict[vol.Optional(CONF_REQUIRED, default=False)] = bool

        return self.async_show_form(
            step_id="add_tag",
            data_schema=vol.Schema(schema_dict),
            errors=errors
        )

    async def async_step_remove_tag(self, user_input=None):
        """Remove a tag from the configuration."""
        if not self.entry_data[CONF_TAGS]:
            return await self.async_step_manage_tags()

        if user_input is not None:
            tags_to_remove = user_input.get("tags_to_remove", [])
            self.entry_data[CONF_TAGS] = [
                tag for tag in self.entry_data[CONF_TAGS]
                if tag[CONF_TAG_ID] not in tags_to_remove
            ]
            return await self.async_step_manage_tags()

        tag_options = {
            tag[CONF_TAG_ID]: f"{tag[CONF_NAME]} ({tag[CONF_TAG_ID]})"
            for tag in self.entry_data[CONF_TAGS]
        }

        data_schema = vol.Schema(
            {
                vol.Required("tags_to_remove"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": k, "label": v} for k, v in tag_options.items()],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN
                    )
                )
            }
        )

        return self.async_show_form(step_id="remove_tag", data_schema=data_schema)

    async def async_step_finish(self, user_input=None):
        """Finish the flow and create config entry."""
        return self.async_create_entry(
            title=self.entry_data["title"],
            data=self.entry_data
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return InteractiveScavengerHuntOptionsFlowHandler(config_entry)


class InteractiveScavengerHuntOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the integration."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        super().__init__()
        self._config_entry = config_entry
        self.options = {
            "title": config_entry.data.get("title", "Interactive Scavenger Hunt"),
            CONF_LIGHTS: list(config_entry.data.get(CONF_LIGHTS, [])),
            CONF_MEDIA_PLAYER: config_entry.data.get(CONF_MEDIA_PLAYER),
            CONF_TAGS: [dict(t) for t in config_entry.data.get(CONF_TAGS, [])],
        }

    def _get_registered_tags_options(self):
        """Get options for registered tags dropdown from Home Assistant's Tag registry."""
        options = []
        tag_store = self.hass.data.get("tag")
        if tag_store:
            from homeassistant.helpers import entity_registry as er
            entity_registry = er.async_get(self.hass)
            
            for item in tag_store.async_items():
                tag_id = item.get("id")
                if not tag_id:
                    continue
                name = f"Tag {tag_id}"
                entity_id = entity_registry.async_get_entity_id("tag", "tag", tag_id)
                if entity_id:
                    entity = entity_registry.async_get(entity_id)
                    if entity:
                        name = entity.name or entity.original_name or name
                options.append({"value": tag_id, "label": f"{name} ({tag_id})"})
        return options

    async def async_step_init(self, user_input=None):
        """Manage options flow entry point."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["edit_settings", "add_tag", "remove_tag"]
        )

    async def async_step_edit_settings(self, user_input=None):
        """Edit basic configurations."""
        if user_input is not None:
            self.options[CONF_LIGHTS] = user_input.get(CONF_LIGHTS, [])
            self.options[CONF_MEDIA_PLAYER] = user_input.get(CONF_MEDIA_PLAYER)
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=self.options
            )
            return self.async_create_entry(title="", data={})

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_LIGHTS, default=self.options.get(CONF_LIGHTS, [])): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="light", multiple=True)
                ),
                vol.Optional(CONF_MEDIA_PLAYER, default=self.options.get(CONF_MEDIA_PLAYER)): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="media_player", multiple=False)
                ),
            }
        )

        return self.async_show_form(step_id="edit_settings", data_schema=data_schema)

    async def async_step_add_tag(self, user_input=None):
        """Add a new tag in options flow."""
        errors = {}
        if user_input is not None:
            tag_id = user_input.get(CONF_TAG_ID) or user_input.get("selected_tag")
            if not tag_id:
                errors["base"] = "missing_tag_id"
            else:
                if CONF_TAGS not in self.options:
                    self.options[CONF_TAGS] = []
                self.options[CONF_TAGS].append({
                    CONF_TAG_ID: tag_id,
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_REQUIRED: user_input.get(CONF_REQUIRED, False),
                })
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=self.options
                )
                return self.async_create_entry(title="", data={})

        registered_tags = self._get_registered_tags_options()
        schema_dict = {}
        if registered_tags:
            schema_dict[vol.Optional("selected_tag")] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=registered_tags,
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            )
            schema_dict[vol.Optional(CONF_TAG_ID)] = str
        else:
            schema_dict[vol.Required(CONF_TAG_ID)] = str

        schema_dict[vol.Required(CONF_NAME)] = str
        schema_dict[vol.Optional(CONF_REQUIRED, default=False)] = bool

        return self.async_show_form(
            step_id="add_tag",
            data_schema=vol.Schema(schema_dict),
            errors=errors
        )

    async def async_step_remove_tag(self, user_input=None):
        """Remove a tag in options flow."""
        tags = self.options.get(CONF_TAGS, [])
        if not tags:
            return self.async_create_entry(title="", data={})

        if user_input is not None:
            tags_to_remove = user_input.get("tags_to_remove", [])
            self.options[CONF_TAGS] = [
                tag for tag in tags
                if tag[CONF_TAG_ID] not in tags_to_remove
            ]
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=self.options
            )
            return self.async_create_entry(title="", data={})

        tag_options = {
            tag[CONF_TAG_ID]: f"{tag[CONF_NAME]} ({tag[CONF_TAG_ID]})"
            for tag in tags
        }

        data_schema = vol.Schema(
            {
                vol.Required("tags_to_remove"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": k, "label": v} for k, v in tag_options.items()],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN
                    )
                )
            }
        )

        return self.async_show_form(step_id="remove_tag", data_schema=data_schema)
