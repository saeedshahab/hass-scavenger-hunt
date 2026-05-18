# Interactive Scavenger Hunt Card

A beautiful, custom Lovelace card designed for scavenger hunts, optimized for TV and tablet displays.

## Features
- **Dynamic Progress**: Displays a sleek score. If the total is revealed via a lifeline, it transforms into a premium progress bar.
- **Glassmorphism Design**: Modern, transparent aesthetic with subtle glow effects and micro-animations.
- **Built-in Audio Engine**: Synthesizes game sounds (success, error, victory) directly in the browser.
- **Victory Mode**: A stunning full-screen overlay when the hunt is completed.
- **Configurable Branding**: Full control over titles and logos.

## Installation

The card is automatically served and registered by the Interactive Scavenger Hunt integration. 

To add it to your dashboard:
1. Ensure the integration is set up in your `configuration.yaml`.
2. Add a **Manual** card to your dashboard.
3. Paste the following configuration:

```yaml
type: custom:scavenger-hunt-card
title: "ADVENTURE"            # Optional: Main header text
completed_title: "FINISHED"  # Optional: Victory screen text
logo_path: "/local/logo.png" # Optional: Custom image logo
# OR
logo_svg: |                  # Optional: Custom SVG logo
  <svg>...</svg>
```

## Setup for TV Casting

For the best experience on a TV:
1. Create a new Dashboard View.
2. Set the **View Type** to `Panel (1 card)`.
3. Add this card to the view.
4. Use Home Assistant Cast or a web browser in fullscreen mode.
