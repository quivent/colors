#!/usr/bin/env python3
"""color - Change terminal foreground/background color."""

import json
import os
import sys

COLORS = {
    "black":   (0, 0, 0),
    "red":     (205, 0, 0),
    "green":   (0, 205, 0),
    "blue":    (0, 0, 238),
    "yellow":  (205, 205, 0),
    "magenta": (205, 0, 205),
    "cyan":    (0, 205, 205),
    "white":   (229, 229, 229),
    "orange":  (255, 165, 0),
    "pink":    (255, 105, 180),
    "purple":  (128, 0, 128),
    "brown":   (139, 69, 19),
    "gray":    (128, 128, 128),
    "grey":    (128, 128, 128),
    "lime":    (0, 255, 0),
    "teal":    (0, 128, 128),
    "navy":    (0, 0, 128),
    "maroon":  (128, 0, 0),
    "olive":   (128, 128, 0),
    "coral":   (255, 127, 80),
    "salmon":  (250, 128, 114),
    "gold":    (255, 215, 0),
    "silver":  (192, 192, 192),
    "sky":     (135, 206, 235),
    "indigo":  (75, 0, 130),
    "violet":  (238, 130, 238),
    "crimson": (220, 20, 60),
    "aqua":    (0, 255, 255),
    "bee":     (218, 165, 0),
    "quantum": (200, 208, 218),
}

_STATE_FILE = os.path.expanduser("~/.color_state.json")


def _load_state():
    try:
        with open(_STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"fg": [229, 229, 229], "bg": [0, 0, 0]}


def _save_state(state):
    with open(_STATE_FILE, "w") as f:
        json.dump(state, f)


# Current working color (set per-invocation from args + persisted state)
_current = {"r": 0, "g": 0, "b": 0, "target": "bg"}


def _clamp(v):
    return max(0, min(255, int(v)))


def _apply():
    r, g, b = _current["r"], _current["g"], _current["b"]
    # OSC 10 = default foreground, OSC 11 = default background
    # These change the terminal's actual colors for the entire session
    osc = 10 if _current["target"] == "fg" else 11
    print(f"\033]{osc};rgb:{r:02x}/{g:02x}/{b:02x}\033\\", end="", flush=True)


def _set_color(r, g, b):
    _current["r"], _current["g"], _current["b"] = r, g, b
    _apply()
    _persist()


def _persist():
    state = _load_state()
    state[_current["target"]] = [_current["r"], _current["g"], _current["b"]]
    _save_state(state)


def _adjust(factor):
    _current["r"] = _clamp(_current["r"] * factor)
    _current["g"] = _clamp(_current["g"] * factor)
    _current["b"] = _clamp(_current["b"] * factor)
    _apply()
    _persist()


def _shift(amount):
    _current["r"] = _clamp(_current["r"] + amount)
    _current["g"] = _clamp(_current["g"] + amount)
    _current["b"] = _clamp(_current["b"] + amount)
    _apply()
    _persist()


def _contrast(r, g, b):
    """Pick black or white text for readability on a given background."""
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return (0, 0, 0) if lum > 128 else (255, 255, 255)


def _show_status():
    r, g, b = _current["r"], _current["g"], _current["b"]
    tgt = _current["target"]
    cr, cg, cb = _contrast(r, g, b)
    # Colored status: swatch block + label rendered in the color
    swatch = f"\033[48;2;{r};{g};{b}m\033[38;2;{cr};{cg};{cb}m  {tgt} = rgb({r}, {g}, {b})  #{r:02x}{g:02x}{b:02x}  \033[0m"
    print(swatch)


USAGE = """\
color - Terminal color changer

Usage: color <command> [args]

Colors:
  color <name>           Set background to named color
  color fg <name>        Set foreground to named color
  color #rrggbb          Set background to hex color
  color fg #rrggbb       Set foreground to hex color
  color rgb R G B        Set background to RGB values

Adjust:
  color brighten [N]     Brighten by N% (default 20)
  color darken [N]       Darken by N% (default 20)
  color lighten [N]      Add N to each channel (default 30)
  color dim [N]          Subtract N from each channel (default 30)
  color saturate         Push toward most dominant channel
  color invert           Invert current color

Other:
  color reset            Reset terminal to defaults
  color show             Show current color
  color list             List all named colors
  color demo             Show all named colors as swatches

Named colors: """ + ", ".join(
    f"\033[38;2;{COLORS[n][0]};{COLORS[n][1]};{COLORS[n][2]}m{n}\033[0m"
    for n in sorted(COLORS)
)


def cmd_list():
    for name, (r, g, b) in sorted(COLORS.items()):
        cr, cg, cb = _contrast(r, g, b)
        print(f"  \033[48;2;{r};{g};{b}m\033[38;2;{cr};{cg};{cb}m {name:10s} \033[0m"
              f"  \033[38;2;{r};{g};{b}mrgb({r}, {g}, {b})  #{r:02x}{g:02x}{b:02x}\033[0m")


def cmd_demo():
    for name, (r, g, b) in sorted(COLORS.items()):
        cr, cg, cb = _contrast(r, g, b)
        # Foreground colored text + background swatch with sample text
        print(f"  \033[48;2;{r};{g};{b}m\033[38;2;{cr};{cg};{cb}m {name:10s} The quick brown fox jumps over the lazy dog \033[0m")


def cmd_invert():
    _current["r"] = 255 - _current["r"]
    _current["g"] = 255 - _current["g"]
    _current["b"] = 255 - _current["b"]
    _apply()
    _persist()


def cmd_saturate():
    r, g, b = _current["r"], _current["g"], _current["b"]
    mx = max(r, g, b)
    if mx == 0:
        return
    scale = 255 / mx
    _current["r"] = _clamp(r * scale)
    _current["g"] = _clamp(g * scale)
    _current["b"] = _clamp(b * scale)
    _apply()
    _persist()


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(USAGE)
        return

    cmd = args[0].lower()
    rest = args[1:]

    # Load persisted state
    state = _load_state()

    # Target selection (default is background)
    if cmd == "fg" and rest:
        _current["target"] = "fg"
        cmd = rest[0].lower()
        rest = rest[1:]
    elif cmd == "bg" and rest:
        _current["target"] = "bg"
        cmd = rest[0].lower()
        rest = rest[1:]
    else:
        _current["target"] = "bg"

    # Load the persisted color for the active target
    tgt = _current["target"]
    _current["r"], _current["g"], _current["b"] = state.get(tgt, [0, 0, 0])

    # Reset — restore terminal's original fg and bg
    if cmd == "reset":
        print("\033]110;\033\\", end="", flush=True)  # reset fg
        print("\033]111;\033\\", end="", flush=True)  # reset bg
        print("\033[0m", end="", flush=True)           # reset SGR attrs
        try:
            os.remove(_STATE_FILE)
        except FileNotFoundError:
            pass
        return

    # Show
    if cmd == "show":
        _show_status()
        return

    # List / demo
    if cmd == "list":
        cmd_list()
        return
    if cmd == "demo":
        cmd_demo()
        return

    # Hex color
    if cmd.startswith("#") and len(cmd) in (4, 7):
        h = cmd[1:]
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        _set_color(r, g, b)
        _show_status()
        return

    # RGB
    if cmd == "rgb" and len(rest) == 3:
        r, g, b = int(rest[0]), int(rest[1]), int(rest[2])
        _set_color(_clamp(r), _clamp(g), _clamp(b))
        _show_status()
        return

    # Brighten / darken
    if cmd == "brighten":
        pct = int(rest[0]) if rest else 20
        _adjust(1 + pct / 100)
        _show_status()
        return
    if cmd == "darken":
        pct = int(rest[0]) if rest else 20
        _adjust(1 - pct / 100)
        _show_status()
        return

    # Lighten / dim (additive)
    if cmd == "lighten":
        amt = int(rest[0]) if rest else 30
        _shift(amt)
        _show_status()
        return
    if cmd == "dim":
        amt = int(rest[0]) if rest else 30
        _shift(-amt)
        _show_status()
        return

    # Invert / saturate
    if cmd == "invert":
        cmd_invert()
        _show_status()
        return
    if cmd == "saturate":
        cmd_saturate()
        _show_status()
        return

    # Named color
    if cmd in COLORS:
        r, g, b = COLORS[cmd]
        _set_color(r, g, b)
        _show_status()
        return

    print(f"Unknown: '{cmd}'. Try 'color help' for usage.")
    sys.exit(1)


if __name__ == "__main__":
    main()
