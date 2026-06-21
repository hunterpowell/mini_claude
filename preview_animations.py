"""Cycle through every pet state for ~2 seconds each. Ctrl-C to stop."""

import json
import time

import config

DURATION = 4.0  # seconds per state


def set_state(state: str):
    config.PET_DIR.mkdir(parents=True, exist_ok=True)
    config.STATE_FILE.write_text(json.dumps({"state": state}))


def main():
    states = config.STATES
    print(f"Previewing {len(states)} states for {DURATION}s each. Ctrl-C to stop.\n")
    try:
        while True:
            for state in states:
                print(f"  {state}")
                set_state(state)
                time.sleep(DURATION)
    except KeyboardInterrupt:
        print("\nDone.")


if __name__ == "__main__":
    main()
