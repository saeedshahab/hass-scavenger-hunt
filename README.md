# Interactive Scavenger Hunt for Home Assistant

A beautiful, interactive scavenger hunt component for Home Assistant. Use NFC tags or QR codes to create an engaging house-wide hunt with real-time feedback, light effects, and a stunning TV-optimized dashboard.

![Scavenger Hunt UI](https://raw.githubusercontent.com/saeedshahab/hass-scavenger-hunt/main/screenshots/dashboard.png)

## Features

- **Real-time Progress**: Track found items on a sleek, modern dashboard.
- **Visual Feedback**: Lights flash and chimes play when a tag is scanned.
- **Built-in Audio Engine**: Generates procedural sound effects directly in the browser (no media files needed).
- **Customizable Branding**: Set your own title, completion message, and logo via YAML.
- **Lifelines**: Interactive hints and skips for difficult hunts.
- **TV Optimized**: Designed to look great on large screens.

## Installation

1. Copy the `custom_components/interactive_scavenger_hunt` directory to your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Add the following to your `configuration.yaml`:

```yaml
interactive_scavenger_hunt:
  lights: light.living_room_group
  media_player: media_player.kitchen_speaker
  tags:
    - tag_id: "NFC_TAG_ID_1"
      name: "The First Clue"
      required: true
    - tag_id: "NFC_TAG_ID_2"
      name: "Under the Sofa"
      required: true
```

## Dashboard Configuration

The dashboard card is automatically registered when the integration is installed. You can add it to your dashboard:

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

- `reset_game`: Reset all progress and lifelines.
- `reveal_total`: Lifeline to show how many tags are left.
- `jump_the_line`: Lifeline to skip the final tag.
- `verify_completion`: Check if the hunt is finished.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT
