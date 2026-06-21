"""Wire the pet into Claude Code by adding hooks to ~/.claude/settings.json.

Each relevant event runs set_state.py, which records the current pet state.
Idempotent: re-running replaces our entries rather than duplicating them.

    python install_hooks.py              # install / refresh
    python install_hooks.py --uninstall  # remove our hooks
"""

import json
import shutil
import sys
from pathlib import Path

import config

SETTINGS = Path.home() / ".claude" / "settings.json"
SCRIPT = config.PROJECT_DIR / "set_state.py"
MARKER = "set_state"  # matches both set_state.py (dev) and set_state.exe (frozen)

# events the pet listens to; PreToolUse filters on tool name and needs a matcher
EVENTS = [
    "UserPromptSubmit",
    "PreToolUse",
    "Notification",
    "Stop",
    "SubagentStop",
    "SessionStart",
    "SessionEnd",
]
NEEDS_MATCHER = {"PreToolUse"}


def command():
    if getattr(sys, 'frozen', False):
        # Running as pet.exe --install; set_state.exe lives next to pet.exe.
        set_state_exe = Path(sys.executable).parent / "set_state.exe"
        return f'"{set_state_exe}"'
    # Dev: use this interpreter explicitly so it works regardless of PATH.
    return f'"{sys.executable}" "{SCRIPT}"'


def make_entry(event):
    hook = {"type": "command", "command": command()}
    entry = {"hooks": [hook]}
    if event in NEEDS_MATCHER:
        entry["matcher"] = "*"
    return entry


def load_settings():
    if SETTINGS.exists():
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    return {}


def strip_ours(hooks_for_event):
    """Drop any entries that point at our set_state.py."""
    kept = []
    for entry in hooks_for_event:
        cmds = " ".join(h.get("command", "") for h in entry.get("hooks", []))
        if MARKER not in cmds:
            kept.append(entry)
    return kept


def save(settings):
    if SETTINGS.exists():
        shutil.copy2(SETTINGS, SETTINGS.with_suffix(".json.bak"))
    SETTINGS.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def main():
    uninstall = "--uninstall" in sys.argv
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})

    # Strip our hooks from every event present, including ones we no longer
    # install (e.g. PostToolUse), so re-running cleans up stale entries.
    for event in list(hooks.keys()):
        kept = strip_ours(hooks[event])
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]

    if not uninstall:
        for event in EVENTS:
            hooks.setdefault(event, []).append(make_entry(event))

    if not hooks:
        settings.pop("hooks", None)

    save(settings)
    action = "Removed" if uninstall else "Installed"
    print(f"{action} pet hooks in {SETTINGS}")
    print(f"Backup written to {SETTINGS.with_suffix('.json.bak')}")
    if not uninstall:
        print("\nRestart any running Claude Code sessions to pick up the hooks.")


if __name__ == "__main__":
    main()
