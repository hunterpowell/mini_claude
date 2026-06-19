"""Hook target: translate a Claude Code hook event into a pet state.

Claude Code pipes the event as JSON on stdin (fields: hook_event_name,
tool_name, ...). This derives a pet state and writes it to STATE_FILE.

Usage from a hook:   python set_state.py
Manual testing:      python set_state.py reading

Always exits 0 and never blocks, so it can't interfere with Claude Code.
"""

import json
import os
import sys
import time

import config


def derive_state(data, argv):
    # explicit override for manual testing: `python set_state.py <state>`
    if len(argv) > 1 and argv[1] in config.STATES:
        return argv[1], argv[1]

    event = data.get("hook_event_name", "")
    tool = data.get("tool_name", "")

    if event == "PreToolUse":
        return config.TOOL_STATE.get(tool, "thinking"), tool
    if event in config.EVENT_STATE:
        return config.EVENT_STATE[event], tool
    # Unrecognized event (e.g. PostToolUse): signal "leave the state alone".
    return None, tool


def main():
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    except Exception:
        raw = ""
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {}

    state, tool = derive_state(data, sys.argv)
    if state is None:
        return  # no meaningful state change; leave STATE_FILE untouched

    payload = {
        "state": state,
        "tool": tool,
        "event": data.get("hook_event_name", ""),
        "ts": time.time(),
    }

    try:
        config.PET_DIR.mkdir(parents=True, exist_ok=True)
        tmp = config.STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(tmp, config.STATE_FILE)  # atomic
    except Exception:
        pass  # never let the pet break a Claude Code session


if __name__ == "__main__":
    main()
    sys.exit(0)
