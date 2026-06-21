"""Shared configuration for the Claude pet.

The state file lives under ~/.claude so the pet reacts to *any* Claude Code
session regardless of which project it runs in. Sprites live next to this file
so the pet always finds them via __file__.
"""

import sys
from pathlib import Path

# --- Paths -------------------------------------------------------------------
# When bundled by PyInstaller, __file__ is inside a temp extraction dir that
# doesn't contain sprites; use _MEIPASS instead (both pet.exe and set_state.exe
# set sys.frozen, but only pet.exe actually needs SPRITES_DIR).
if getattr(sys, 'frozen', False):
    PROJECT_DIR = Path(sys._MEIPASS)
else:
    PROJECT_DIR = Path(__file__).resolve().parent
SPRITES_DIR = PROJECT_DIR / "sprites"

PET_DIR = Path.home() / ".claude" / "pet"
STATE_FILE = PET_DIR / "state.json"

# --- States ------------------------------------------------------------------
# Every state must have a matching folder under sprites/<state>/ containing
# frame_00.png, frame_01.png, ... Replace the temp art with your own anytime;
# just keep the folder names (or edit them here + re-run install_hooks).
STATES = [
    "idle",      # Claude finished, hanging out
    "thinking",  # processing your prompt / between tools
    "reading",   # Read / Grep / Glob
    "writing",   # Edit / Write / TodoWrite
    "running",   # Bash
    "searching", # WebFetch / WebSearch
    "waiting",   # needs your attention (permission / notification)
    "sleeping",  # idle for a while / session ended
]

DEFAULT_STATE = "sleeping"

# Map a Claude Code tool name to a pet state (used on PreToolUse).
TOOL_STATE = {
    "Read": "reading",
    "Grep": "reading",
    "Glob": "reading",
    "NotebookRead": "reading",
    "LS": "reading",
    "Edit": "writing",
    "Write": "writing",
    "MultiEdit": "writing",
    "NotebookEdit": "writing",
    "TodoWrite": "writing",
    "Bash": "running",
    "BashOutput": "running",
    "KillBash": "running",
    "WebFetch": "searching",
    "WebSearch": "searching",
    "Task": "thinking",
    "AskUserQuestion": "waiting",  # I'm asking you something
    "ExitPlanMode": "waiting",     # waiting on plan approval
}

# Map a hook event name to a state (tools are resolved via TOOL_STATE first).
# PostToolUse and SubagentStop are intentionally absent: the pet lingers on the
# tool's state until the next real action instead of bouncing back between tools.
EVENT_STATE = {
    "UserPromptSubmit": "thinking",
    "Notification": "waiting",
    "Stop": "idle",
    "SessionStart": "idle",
    "SessionEnd": "sleeping",
}

# --- Animation / window tuning ----------------------------------------------
FRAME_MS = 180          # ms between sprite frames
SCALE = 3               # pixel-art upscale factor (nearest-neighbor)
POLL_MS = 120           # how often the pet checks the state file
MIN_DWELL_SEC = 0.6     # min time a state stays visible before the next one
MAX_QUEUE = 3           # cap pending states so the pet can't lag behind reality
IDLE_TO_SLEEP_SEC = 60  # drift idle -> sleeping after this many seconds
MARGIN = 24             # px gap from the screen corner
CORNER = "bottom-right" # bottom-right | bottom-left | top-right | top-left
