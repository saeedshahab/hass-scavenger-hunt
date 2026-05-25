import logging
import time
import asyncio
import voluptuous as vol
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.components.persistent_notification import async_create
from homeassistant.const import CONF_NAME, EVENT_HOMEASSISTANT_START
import os

from .const import (
    DOMAIN,
    CONF_TAGS,
    CONF_TAG_ID,
    CONF_REQUIRED,
    CONF_LIGHTS,
    CONF_MEDIA_PLAYER,
    EVENT_HUNT_UPDATE,
    EVENT_TAG_SCANNED,
    SERVICE_REVEAL_TOTAL,
    SERVICE_JUMP_THE_LINE,
    SERVICE_GUESS_BYPASS,
    SERVICE_RESET_GAME,
    SERVICE_VERIFY_COMPLETION,
    SERVICE_PLAY_SOUND,
    ATTR_SCORE,
    ATTR_LAST_TAG,
    ATTR_LIFELINES,
)

_LOGGER = logging.getLogger(__name__)

TAG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TAG_ID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_REQUIRED, default=False): cv.boolean,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_TAGS): vol.All(cv.ensure_list, [TAG_SCHEMA]),
                vol.Optional(CONF_LIGHTS): cv.ensure_list,
                vol.Optional(CONF_MEDIA_PLAYER): cv.entity_id,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the scavenger hunt integration."""
    conf = config.get(DOMAIN)
    if conf is None:
        return True

    tags_config = conf[CONF_TAGS]
    lights = conf.get(CONF_LIGHTS, [])
    media_player = conf.get(CONF_MEDIA_PLAYER)
    
    manager = ScavengerHuntManager(hass, tags_config, lights, media_player)
    hass.data[DOMAIN] = manager

    # Register static path for the dashboard card
    card_path = hass.config.path(f"custom_components/{DOMAIN}/dashboard/scavenger-hunt-card.js")
    if os.path.exists(card_path):
        hass.http.register_static_path("/scavenger-hunt-card.js", card_path)
        _LOGGER.debug("Registered static path for scavenger-hunt-card.js")

    # Automatically register Lovelace resource
    async def async_register_lovelace_resource(event):
        """Register Lovelace resource when Home Assistant starts."""
        if "lovelace" not in hass.data:
            return

        resources = hass.data["lovelace"].get("resources")
        if resources:
            # Check if already registered
            url = "/scavenger-hunt-card.js"
            if not any(res.get("url") == url for res in resources.async_items()):
                _LOGGER.info("Automatically registering Lovelace resource for Scavenger Hunt Card")
                if hasattr(resources, "async_create_item"):
                    await resources.async_create_item({"res_type": "module", "url": url})

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, async_register_lovelace_resource)

    # Register services
    async def handle_reveal_total(call):
        await manager.reveal_total()

    async def handle_jump_the_line(call):
        await manager.jump_the_line()

    async def handle_guess_bypass(call):
        guess = call.data.get("guess")
        await manager.guess_bypass(guess)

    async def handle_reset_game(call):
        await manager.reset_game()

    async def handle_verify_completion(call):
        await manager.verify_completion()

    async def handle_play_sound(call):
        sound_type = call.data.get("sound_type")
        await manager.play_sound(sound_type)

    hass.services.async_register(DOMAIN, SERVICE_REVEAL_TOTAL, handle_reveal_total)
    hass.services.async_register(DOMAIN, SERVICE_JUMP_THE_LINE, handle_jump_the_line)
    hass.services.async_register(DOMAIN, SERVICE_RESET_GAME, handle_reset_game)
    hass.services.async_register(DOMAIN, SERVICE_VERIFY_COMPLETION, handle_verify_completion)
    hass.services.async_register(DOMAIN, SERVICE_PLAY_SOUND, handle_play_sound)
    hass.services.async_register(
        DOMAIN, 
        SERVICE_GUESS_BYPASS, 
        handle_guess_bypass,
        schema=vol.Schema({vol.Required("guess"): cv.positive_int})
    )

    # Listen for tag scans
    @callback
    def async_tag_scanned(event):
        tag_id = event.data.get("tag_id")
        if tag_id:
            hass.async_create_task(manager.process_tag(tag_id))

    hass.bus.async_listen(EVENT_TAG_SCANNED, async_tag_scanned)

    # Load platforms
    hass.async_create_task(async_load_platform(hass, "sensor", DOMAIN, {}, config))
    hass.async_create_task(async_load_platform(hass, "binary_sensor", DOMAIN, {}, config))

    return True

class ScavengerHuntManager:
    """Manages the scavenger hunt state."""

    def __init__(self, hass, tags_config, lights=None, media_player=None):
        self.hass = hass
        self.tags_config = {t[CONF_TAG_ID]: t for t in tags_config}
        self.total_tags_count = len(tags_config)
        self.scanned_tags = set()
        self.bypass_attempted = False
        self.game_completed = False
        self.last_tag = None
        self.revealed_total = False
        self.lights = lights or []
        self.media_player = media_player
        self.last_verify_failed = None
        self.last_sound_event = None
        
        # Capture initial light states for reset
        self.initial_light_states = {}
        for entity_id in self.lights:
            state = self.hass.states.get(entity_id)
            if state:
                self.initial_light_states[entity_id] = {
                    "state": state.state,
                    "attributes": self._get_light_params(state)
                }

        # Identify "required" tags for bypass (using YAML flag)
        self.required_tags = {
            tid for tid, cfg in self.tags_config.items() if cfg.get(CONF_REQUIRED)
        }

    def _get_light_params(self, state):
        """Extract valid restoration parameters from light state."""
        params = {}
        if "brightness" in state.attributes:
            params["brightness"] = state.attributes["brightness"]
            
        color_mode = state.attributes.get("color_mode")
        
        # Priority mapping for color modes
        if color_mode == "color_temp":
            params["color_temp"] = state.attributes.get("color_temp")
        elif color_mode == "rgb":
            params["rgb_color"] = state.attributes.get("rgb_color")
        elif color_mode == "xy":
            params["xy_color"] = state.attributes.get("xy_color")
        elif color_mode == "hs":
            params["hs_color"] = state.attributes.get("hs_color")
        elif color_mode == "rgbw":
            params["rgbw_color"] = state.attributes.get("rgbw_color")
        elif color_mode == "rgbww":
            params["rgbww_color"] = state.attributes.get("rgbww_color")
        else:
            # Fallback for older lights or unknown modes
            # Try to pick just one color attribute to avoid validation errors
            for attr in ["rgb_color", "xy_color", "hs_color", "color_temp"]:
                if attr in state.attributes:
                    params[attr] = state.attributes[attr]
                    break
        
        # Filter out None values to be safe
        return {k: v for k, v in params.items() if v is not None}

    async def _flash_lights(self, color_name):
        """Flash configured lights and restore state."""
        if not self.lights:
            return
        
        # Capture current states
        states = {}
        for entity_id in self.lights:
            state = self.hass.states.get(entity_id)
            if state:
                states[entity_id] = {
                    "state": state.state,
                    "attributes": self._get_light_params(state)
                }

        # Turn on with flash color
        try:
            await self.hass.services.async_call(
                "light", "turn_on", 
                {"entity_id": self.lights, "color_name": color_name, "brightness": 255}
            )
        except Exception as e:
            _LOGGER.error("Failed to flash lights: %s", e)
        
        # Wait for "flash" effect
        await asyncio.sleep(2)
        
        # Restore states
        for entity_id, saved in states.items():
            try:
                if saved["state"] == "off":
                    await self.hass.services.async_call("light", "turn_off", {"entity_id": entity_id})
                else:
                    service_data = {"entity_id": entity_id, **saved["attributes"]}
                    await self.hass.services.async_call("light", "turn_on", service_data)
            except Exception as e:
                _LOGGER.error("Failed to restore light %s: %s", entity_id, e)

    async def play_sound(self, sound_type):
        """Update the sound event attribute for the dashboard."""
        self.last_sound_event = {
            "type": sound_type,
            "timestamp": time.time()
        }
        self._notify_update()

    async def process_tag(self, tag_id):
        """Process a scanned tag."""
        if tag_id not in self.tags_config:
            # Not a game tag
            return

        if tag_id in self.scanned_tags:
            # Already scanned - Failure indication
            await self._flash_lights("red")
            await self.play_sound("error")
            return

        # New successful scan
        self.scanned_tags.add(tag_id)
        self.last_tag = self.tags_config[tag_id][CONF_NAME]
        
        await self._flash_lights("green")
        await self.play_sound("success")
        
        # Auto-verify if total is revealed and we just found the last one
        if self.revealed_total and len(self.scanned_tags) >= self.total_tags_count:
            await self.verify_completion()
            
        self._notify_update()

    def _notify_update(self):
        """Fire update event and refresh entities."""
        lifelines = []
        score = len(self.scanned_tags)
        total = self.total_tags_count

        # At most ONE lifeline available
        if score < (total - 2):
            if (self.required_tags and 
                self.required_tags.issubset(self.scanned_tags) and 
                not self.bypass_attempted):
                lifelines.append(SERVICE_GUESS_BYPASS)
        elif not self.revealed_total:
            # Score is >= total - 2, and not revealed yet
            lifelines.append(SERVICE_REVEAL_TOTAL)
        elif score == (total - 1):
            # Score is exactly total - 1 and revealed
            lifelines.append(SERVICE_JUMP_THE_LINE)

        self.hass.bus.async_fire(
            EVENT_HUNT_UPDATE,
            {
                ATTR_SCORE: score,
                ATTR_LAST_TAG: self.last_tag,
                ATTR_LIFELINES: lifelines,
            },
        )
        async_dispatcher_send(self.hass, f"{DOMAIN}_update")

    async def verify_completion(self):
        """Service to check if game is complete."""
        if len(self.scanned_tags) >= self.total_tags_count:
            self.game_completed = True
            await self._flash_lights("blue") # Celebrate
            await self.play_sound("victory")
        else:
            self.last_verify_failed = time.time()
            await self._flash_lights("red")
            await self.play_sound("error")
            async_create(
                self.hass,
                "Keep looking! You haven't found everything yet.",
                title="Verification Failed"
            )
        
        # Always notify so sensors and dashboard update
        self._notify_update()

    async def reveal_total(self):
        """Service to reveal the total number of tags."""
        score = len(self.scanned_tags)
        if score >= (self.total_tags_count - 2):
            self.revealed_total = True
            async_create(
                self.hass,
                f"The total number of tags to find is {self.total_tags_count}.",
                title="Lifeline: Total Revealed"
            )
            
            # Edge case: If they already have everything, auto-verify now that they know.
            if score >= self.total_tags_count:
                await self.verify_completion()
                
            self._notify_update()

    async def jump_the_line(self):
        """Service to skip the last tag."""
        if not self.revealed_total:
            return
            
        score = len(self.scanned_tags)
        if score == (self.total_tags_count - 1):
            # Find a tag that hasn't been scanned
            all_ids = set(self.tags_config.keys())
            remaining = all_ids - self.scanned_tags
            if remaining:
                skipped_id = list(remaining)[0]
                self.scanned_tags.add(skipped_id)
                self.last_tag = "Lifeline: Jump the Line"
                # Auto-verify since Jump the Line always finishes the collection
                await self.verify_completion()
                self._notify_update()

    async def guess_bypass(self, guess):
        """Service for the one-time bypass attempt."""
        if self.bypass_attempted:
            _LOGGER.warning("Bypass already attempted")
            return

        score = len(self.scanned_tags)
        total = self.total_tags_count
        
        # Check if required tags are met (if any exist)
        req_met = not self.required_tags or self.required_tags.issubset(self.scanned_tags)
        
        _LOGGER.debug("Bypass Check: score=%s, total=%s, req_met=%s", score, total, req_met)

        if req_met and score < (total - 2):
            self.bypass_attempted = True
            if guess == total:
                _LOGGER.info("Bypass Successful! Guessed %s", guess)
                all_ids = set(self.tags_config.keys())
                self.scanned_tags = all_ids
                self.last_tag = "Bypass Success"
                await self.verify_completion()
            else:
                _LOGGER.info("Bypass Failed! Guessed %s, actual %s", guess, total)
                await self.play_sound("error")
                async_create(
                    self.hass,
                    "Wrong guess! The bypass option is now gone forever.",
                    title="Bypass Failed"
                )
            self._notify_update()
        else:
            _LOGGER.warning("Bypass conditions not met: req_met=%s, score=%s", req_met, score)

    async def reset_game(self):
        """Reset the game state."""
        self.scanned_tags = set()
        self.bypass_attempted = False
        self.game_completed = False
        self.last_tag = None
        self.revealed_total = False
        
        # Restore lights to initial state
        for entity_id, saved in self.initial_light_states.items():
            try:
                if saved["state"] == "off":
                    await self.hass.services.async_call("light", "turn_off", {"entity_id": entity_id})
                else:
                    service_data = {"entity_id": entity_id, **saved["attributes"]}
                    await self.hass.services.async_call("light", "turn_on", service_data)
            except Exception as e:
                _LOGGER.error("Failed to restore initial light state for %s: %s", entity_id, e)
            
        self._notify_update()
