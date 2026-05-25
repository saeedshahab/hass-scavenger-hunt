# Interactive scavenger hunt for Home Assistant

A beautiful, interactive scavenger hunt component for Home Assistant. Use NFC tags or QR codes to create an engaging house-wide hunt with real-time feedback, light effects, and a stunning TV-optimized dashboard.

![Scavenger Hunt UI](https://raw.githubusercontent.com/saeedshahab/hass-scavenger-hunt/main/screenshots/dashboard.png)

## Features

- **UI-driven configuration**: Set up, customize, and manage tags completely from the Home Assistant interface.
- **Real-time progress**: Track found items on a sleek, modern dashboard card.
- **Visual feedback**: Lights flash and chimes play when a tag is scanned.
- **Built-in audio engine**: Generates procedural sound effects directly in the browser (no media files needed).
- **Native NFC tag integration**: Easily select from NFC tags already registered in your Home Assistant tag registry.
- **Customizable branding**: Set your own title, completion message, and logo.
- **Interactive lifelines**: Hints, bypass guesses, and skips to keep players engaged.
- **TV optimized**: Designed to look great when cast to large screens.

## Installation

1. Copy the `custom_components/interactive_scavenger_hunt` directory to your Home Assistant `custom_components` folder.
2. Restart Home Assistant.

### Option A: Configuration via UI (recommended)

1. Navigate to **Settings** > **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **"Interactive Scavenger Hunt"** and select it.
4. Follow the step-by-step setup to:
   - Name your hunt.
   - Select the target lights to flash.
   - Choose a speaker for sound effects.
   - Add your tags (you can pick from your **existing registered tags** in the dropdown or type in custom tag payloads manually).
5. **Managing tags/settings later**: Click **Configure** on the integration card at any time to add new tags, remove tags, or edit light/speaker settings.

### Option B: Configuration via YAML (advanced)

For advanced users, you can optionally configure the hunt inside your `configuration.yaml`:

```yaml
interactive_scavenger_hunt:
  lights: 
    - light.living_room_group
  media_player: media_player.kitchen_speaker
  tags:
    - tag_id: "NFC_TAG_ID_1"
      name: "The first clue"
      required: true
    - tag_id: "NFC_TAG_ID_2"
      name: "Under the sofa"
      required: true
```

## Dashboard configuration

The dashboard card is automatically registered when the integration is installed. You can add it to your Lovelace dashboard:

```yaml
type: custom:scavenger-hunt-card
title: "THE BIG ADVENTURE"
completed_title: "VICTORY ACHIEVED"
logo_svg: |
  <svg>...</svg> # Optional custom SVG
# OR
logo_path: "/local/my_logo.png"
```

## Services

- `reset_game`: Reset the game progress, clear all scanned tags, and restore all lifelines.
- `reveal_total`: Reveal the total number of tags in the game (available when only 2 tags are left).
- `jump_the_line`: Skip the last remaining tag (available when the total is revealed and only 1 tag is left).
- `guess_bypass`: Make a one-time attempt to complete the game early by guessing the total number of tags.
- `verify_completion`: Check if all tags have been scanned and mark the game as completed.
- `play_sound`: Play a success, error, or victory sound effect manually on the dashboard.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on the [GitHub repository](https://github.com/saeedshahab/hass-scavenger-hunt).

## License

MIT
