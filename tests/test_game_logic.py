import asyncio
import pytest
from unittest.mock import MagicMock, patch
from custom_components.interactive_scavenger_hunt.__init__ import ScavengerHuntManager
from custom_components.interactive_scavenger_hunt.const import (
    CONF_TAG_ID,
    CONF_NAME,
    CONF_REQUIRED,
    SERVICE_REVEAL_TOTAL,
    SERVICE_JUMP_THE_LINE,
    SERVICE_GUESS_BYPASS,
)

@pytest.fixture
def hass():
    """Mock Hass object."""
    mock = MagicMock()
    mock.bus.async_fire = MagicMock()
    mock.helpers.dispatcher.async_dispatcher_send = MagicMock()
    mock.components.persistent_notification.create = MagicMock()
    return mock

@pytest.fixture
def tags_config():
    """Sample tags config with 20 tags."""
    tags = []
    for i in range(20):
        tags.append({
            CONF_TAG_ID: f"tag_{i}",
            CONF_NAME: f"Tag Name {i}",
            CONF_REQUIRED: i < 11  # First 11 are required
        })
    return tags

@pytest.fixture
def manager(hass, tags_config):
    """ScavengerHuntManager instance."""
    # Assuming tests don't pass lights/media player
    return ScavengerHuntManager(hass, tags_config)

@pytest.mark.asyncio
async def test_basic_scoring(manager, hass):
    """Test that scanning tags increments score."""
    await manager.process_tag("tag_0")
    assert len(manager.scanned_tags) == 1
    assert manager.last_tag == "Tag Name 0"
    
    # Duplicate scan
    await manager.process_tag("tag_0")
    assert len(manager.scanned_tags) == 1
    
    # Multiple unique scans
    await manager.process_tag("tag_1")
    await manager.process_tag("tag_2")
    assert len(manager.scanned_tags) == 3

@pytest.mark.asyncio
async def test_reveal_total_lifeline(manager, hass):
    """Test reveal total logic (score == total - 2)."""
    for i in range(17):
        await manager.process_tag(f"tag_{i}")
    
    assert manager.revealed_total is False
    
    # Scan 18th tag
    await manager.process_tag("tag_17")
    assert len(manager.scanned_tags) == 18
    
    # Now it should work
    await manager.reveal_total()
    assert manager.revealed_total is True

@pytest.mark.asyncio
async def test_jump_the_line(manager, hass):
    """Test jump the line logic (score == total - 1)."""
    for i in range(19):
        await manager.process_tag(f"tag_{i}")
    
    assert len(manager.scanned_tags) == 19
    
    # Must reveal total before jump the line is allowed
    await manager.reveal_total()
    
    await manager.jump_the_line()
    assert len(manager.scanned_tags) == 20
    # Game is NOT automatically completed anymore without verify
    assert manager.game_completed is False
    
    await manager.verify_completion()
    assert manager.game_completed is True

@pytest.mark.asyncio
async def test_bypass_success(manager, hass):
    """Test bypass success logic."""
    for i in range(11):
        await manager.process_tag(f"tag_{i}")
    
    await manager.guess_bypass(20)
    
    assert len(manager.scanned_tags) == 20
    assert manager.bypass_attempted is True
    assert manager.game_completed is True # Bypass auto verifies

@pytest.mark.asyncio
async def test_bypass_failure(manager, hass):
    """Test bypass failure logic."""
    for i in range(11):
        await manager.process_tag(f"tag_{i}")
    
    await manager.guess_bypass(21)
    
    assert manager.game_completed is False
    assert manager.bypass_attempted is True
    
    # Attempt again
    await manager.guess_bypass(20)
    assert manager.game_completed is False

@pytest.mark.asyncio
async def test_verify_completion_fails(manager, hass):
    """Test verification fails if not all tags scanned."""
    for i in range(19):
        await manager.process_tag(f"tag_{i}")
        
    await manager.verify_completion()
    assert manager.game_completed is False
    hass.components.persistent_notification.create.assert_called_with(
        "Keep looking! You haven't found everything yet.",
        title="Verification Failed"
    )

@pytest.mark.asyncio
async def test_reset(manager, hass):
    """Test reset logic."""
    await manager.process_tag("tag_0")
    await manager.reset_game()
    assert len(manager.scanned_tags) == 0
    assert manager.game_completed is False

@pytest.mark.asyncio
async def test_update_events(manager, hass):
    """Test that events are fired on updates."""
    await manager.process_tag("tag_0")
    hass.bus.async_fire.assert_called()
    hass.helpers.dispatcher.async_dispatcher_send.assert_called_with("interactive_scavenger_hunt_update")

