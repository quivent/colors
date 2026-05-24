#!/usr/bin/env python3
"""color - Change terminal foreground/background color."""

import base64
import json
import os
import plistlib
import subprocess
import sys
import time

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

iTerm2:
  color theme <name>     Set iTerm2 color preset
  color themes           List available color presets
  color preview [delay]  Cycle through all presets
  color profile <name>   Switch iTerm2 profile
  color profiles         List available profiles
  color tab <color>      Set tab bar color
  color tab reset        Reset tab color
  color cursor <color>   Set cursor color
  color cursor block     Set cursor shape (block|bar|underline)
  color badge <text>     Set badge text
  color badge clear      Clear badge
  color set <slot> <c>   Set individual color slot
  color transparency <N> Set window transparency 0-100
  color blur <N>         Set background blur 0-100

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


def _require_iterm(cmd_name):
    if os.environ.get("TERM_PROGRAM") != "iTerm2":
        print(f"Error: '{cmd_name}' requires iTerm2.")
        sys.exit(1)


def _iterm_esc(payload):
    """Send an iTerm2 proprietary escape sequence."""
    print(f"\033]{payload}\a", end="", flush=True)


def _resolve_color_arg(args):
    """Parse a color from args: named color, hex, or R G B. Returns (r,g,b) and remaining args."""
    if not args:
        return None, args
    token = args[0].lower()
    if token in COLORS:
        return COLORS[token], args[1:]
    if token.startswith("#") and len(token) in (4, 7):
        h = token[1:]
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)), args[1:]
    if len(args) >= 3:
        try:
            return (_clamp(int(args[0])), _clamp(int(args[1])), _clamp(int(args[2]))), args[3:]
        except ValueError:
            pass
    return None, args


# --- iTerm2 SetColors keys ---
ITERM_COLOR_KEYS = {
    "fg": "fg", "bg": "bg", "bold": "bold", "link": "link",
    "selbg": "selbg", "selfg": "selfg", "curbg": "curbg", "curfg": "curfg",
    "underline": "underline", "tab": "tab",
    "black": "black", "red": "red", "green": "green", "yellow": "yellow",
    "blue": "blue", "magenta": "magenta", "cyan": "cyan", "white": "white",
    "brblack": "br_black", "brred": "br_red", "brgreen": "br_green",
    "bryellow": "br_yellow", "brblue": "br_blue", "brmagenta": "br_magenta",
    "brcyan": "br_cyan", "brwhite": "br_white",
}


def _get_iterm_presets():
    """Read available color presets from iTerm2 preferences."""
    plist_path = os.path.expanduser(
        "~/Library/Preferences/com.googlecode.iterm2.plist"
    )
    try:
        result = subprocess.run(
            ["plutil", "-convert", "xml1", "-o", "-", plist_path],
            capture_output=True,
        )
        if result.returncode != 0:
            return []
        data = plistlib.loads(result.stdout)
        presets = data.get("Custom Color Presets", {})
        return sorted(presets.keys())
    except (FileNotFoundError, Exception):
        return []


def _get_iterm_profiles():
    """Read profile names from iTerm2 preferences."""
    plist_path = os.path.expanduser(
        "~/Library/Preferences/com.googlecode.iterm2.plist"
    )
    try:
        result = subprocess.run(
            ["plutil", "-convert", "xml1", "-o", "-", plist_path],
            capture_output=True,
        )
        if result.returncode != 0:
            return []
        data = plistlib.loads(result.stdout)
        bookmarks = data.get("New Bookmarks", [])
        return sorted(b.get("Name", "?") for b in bookmarks)
    except (FileNotFoundError, Exception):
        return []


def cmd_theme(name):
    _require_iterm("theme")
    _iterm_esc(f"1337;SetColors=preset={name}")
    print(f"Theme: {name}")


def cmd_themes():
    _require_iterm("themes")
    presets = _get_iterm_presets()
    if not presets:
        print("No custom presets found. Built-in presets are always available:")
        print("  Try: color theme 'Solarized Dark'")
        return
    print("Available iTerm2 color presets:")
    for name in presets:
        print(f"  {name}")


def cmd_profile(name):
    _require_iterm("profile")
    _iterm_esc(f"1337;SetProfile={name}")
    print(f"Profile: {name}")


def cmd_profiles():
    _require_iterm("profiles")
    profiles = _get_iterm_profiles()
    if not profiles:
        print("No profiles found.")
        return
    print("Available iTerm2 profiles:")
    for name in profiles:
        print(f"  {name}")


def cmd_tab(args):
    """Set or reset the iTerm2 tab color."""
    _require_iterm("tab")
    if not args or args[0].lower() == "reset":
        _iterm_esc("6;1;bg;*;default")
        print("Tab color reset.")
        return
    rgb, _ = _resolve_color_arg(args)
    if rgb is None:
        print("Usage: color tab <color|reset>")
        sys.exit(1)
    r, g, b = rgb
    _iterm_esc(f"6;1;bg;red;brightness;{r}")
    _iterm_esc(f"6;1;bg;green;brightness;{g}")
    _iterm_esc(f"6;1;bg;blue;brightness;{b}")
    print(f"Tab color: rgb({r}, {g}, {b})")


def cmd_cursor(args):
    """Change cursor color or shape."""
    _require_iterm("cursor")
    if not args:
        print("Usage: color cursor <color> | color cursor block|bar|underline")
        sys.exit(1)
    shapes = {"block": 0, "bar": 1, "line": 1, "underline": 2}
    token = args[0].lower()
    if token in shapes:
        _iterm_esc(f"1337;CursorShape={shapes[token]}")
        print(f"Cursor shape: {token}")
        return
    rgb, _ = _resolve_color_arg(args)
    if rgb is None:
        print(f"Unknown cursor option: {args[0]}")
        sys.exit(1)
    r, g, b = rgb
    _iterm_esc(f"1337;SetColors=curbg={r:02x}{g:02x}{b:02x}")
    print(f"Cursor color: rgb({r}, {g}, {b})")


def cmd_badge(args):
    """Set or clear the iTerm2 badge."""
    _require_iterm("badge")
    if not args or args[0].lower() == "clear":
        _iterm_esc("1337;SetBadgeFormat=")
        print("Badge cleared.")
        return
    text = " ".join(args)
    encoded = base64.b64encode(text.encode()).decode()
    _iterm_esc(f"1337;SetBadgeFormat={encoded}")
    print(f"Badge: {text}")


def cmd_setcolor(args):
    """Set an individual iTerm2 color slot: color set <slot> <color>."""
    _require_iterm("set")
    if len(args) < 2:
        print("Usage: color set <slot> <color>")
        print("Slots: " + ", ".join(sorted(ITERM_COLOR_KEYS.keys())))
        sys.exit(1)
    slot = args[0].lower()
    if slot not in ITERM_COLOR_KEYS:
        print(f"Unknown slot '{slot}'. Available: {', '.join(sorted(ITERM_COLOR_KEYS.keys()))}")
        sys.exit(1)
    rgb, _ = _resolve_color_arg(args[1:])
    if rgb is None:
        print(f"Can't parse color from: {' '.join(args[1:])}")
        sys.exit(1)
    r, g, b = rgb
    key = ITERM_COLOR_KEYS[slot]
    _iterm_esc(f"1337;SetColors={key}={r:02x}{g:02x}{b:02x}")
    cr, cg, cb = _contrast(r, g, b)
    swatch = f"\033[48;2;{r};{g};{b}m\033[38;2;{cr};{cg};{cb}m  {slot} = rgb({r}, {g}, {b})  \033[0m"
    print(swatch)


def cmd_preview(args):
    """Cycle through iTerm2 presets with a delay, then revert."""
    _require_iterm("preview")
    delay = 1.5
    if args and args[0].replace(".", "").isdigit():
        delay = float(args[0])
        args = args[1:]
    presets = args if args else _get_iterm_presets()
    if not presets:
        print("No presets to preview.")
        return
    print(f"Previewing {len(presets)} presets ({delay}s each). Ctrl-C to stop.")
    original = None
    try:
        for name in presets:
            if original is None:
                original = name
            _iterm_esc(f"1337;SetColors=preset={name}")
            print(f"  → {name}")
            time.sleep(delay)
    except KeyboardInterrupt:
        print()
    if original:
        _iterm_esc(f"1337;SetColors=preset={original}")
        print(f"Reverted to: {original}")


def cmd_transparency(args):
    """Set window transparency via AppleScript."""
    _require_iterm("transparency")
    if not args:
        print("Usage: color transparency <0-100>")
        sys.exit(1)
    try:
        val = int(args[0])
    except ValueError:
        print("Transparency must be a number 0-100.")
        sys.exit(1)
    val = max(0, min(100, val))
    alpha = val / 100.0
    script = f'''
    tell application "iTerm2"
        tell current session of current window
            set transparency to {alpha}
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script], capture_output=True)
    print(f"Transparency: {val}%")


def cmd_blur(args):
    """Set background blur radius via AppleScript."""
    _require_iterm("blur")
    if not args:
        print("Usage: color blur <0-100>")
        sys.exit(1)
    try:
        val = int(args[0])
    except ValueError:
        print("Blur must be a number 0-100.")
        sys.exit(1)
    val = max(0, min(100, val))
    radius = val / 100.0
    enable = "true" if val > 0 else "false"
    script = f'''
    tell application "iTerm2"
        tell current session of current window
            set use transparency to true
            set blur to {enable}
            set blur radius to {radius}
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script], capture_output=True)
    print(f"Blur: {val}%")


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

    # iTerm2 commands
    if cmd == "themes":
        cmd_themes()
        return
    if cmd == "theme":
        if not rest:
            print("Usage: color theme <preset-name>")
            sys.exit(1)
        cmd_theme(" ".join(rest))
        return
    if cmd == "preview":
        cmd_preview(rest)
        return
    if cmd == "profile":
        if not rest:
            print("Usage: color profile <name>")
            sys.exit(1)
        cmd_profile(" ".join(rest))
        return
    if cmd == "profiles":
        cmd_profiles()
        return
    if cmd == "tab":
        cmd_tab(rest)
        return
    if cmd == "cursor":
        cmd_cursor(rest)
        return
    if cmd == "badge":
        cmd_badge(rest)
        return
    if cmd == "set":
        cmd_setcolor(rest)
        return
    if cmd == "transparency":
        cmd_transparency(rest)
        return
    if cmd == "blur":
        cmd_blur(rest)
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
