# Mini Claude

A little 8-bit critter that lives in the corner of your screen and plays
animations reflecting what Claude Code is currently doing; reading files,
editing, running commands, searching the web, waiting on you, or napping when
idle.

It works by hooking into Claude Code's event system. Each event runs a tiny
script that records the current "state" to a file; the pet watches that file
and switches animation. Because the state file lives under `~/.claude`, the pet
reacts to **any** Claude Code session, in any project.

```
  Claude Code event ──hook──> set_state.py ──> ~/.claude/pet/state.json
                                                        │ (watched)
                                                        ▼
                                                     pet.py 
```

## States

| State      | Triggered by                                   |
|------------|------------------------------------------------|
| `thinking` | you submit a prompt; between tool calls        |
| `reading`  | Read / Grep / Glob                             |
| `writing`  | Edit / Write / TodoWrite                        |
| `running`  | Bash                                            |
| `searching`| WebFetch / WebSearch                            |
| `waiting`  | Claude needs your attention (permission, etc.) |
| `idle`     | Claude finished responding                      |
| `sleeping` | idle for a while / session ended               |

## Python

Built and tested on **Python 3.12**; the commands below use `py -3.12`.
(`set_state.py` is pure stdlib and runs anywhere; only the pet window needs
PyQt6.)

## Setup

```powershell
# 1. install deps on the clean interpreter
py -3.12 -m pip install -r requirements.txt

# 2. wire the pet into Claude Code (writes a settings.json.bak first)
py -3.12 install_hooks.py

# 3. start the pet (no console window)
start_pet.bat
```

Restart any open Claude Code sessions so they pick up the new hooks. Drag the
pet to move it; right-click it for a menu (snap to corner / quit).

## Customizing the art

The sprites under `sprites/` are hand-drawn 8-bit frames. To tweak them or add
your own, drop PNG frames into the matching folder:

```
sprites/<state>/frame_00.png, frame_01.png, frame_02.png, ...
```

- Frames play in filename order at `FRAME_MS` (see `config.py`).
- Native art is upscaled by `SCALE` (default 4×) with nearest-neighbor. If your
  art is already full-size, set `SCALE = 1`.
- Any number of frames per state is fine (even 1).
- A state with no frames falls back to `idle`.

Tunables (corner, margin, frame rate, idle-to-sleep delay) live in `config.py`.

## Uninstall

```powershell
py -3.12 install_hooks.py --uninstall   # restores hooks; backup also at settings.json.bak
```

## Files

| File              | Purpose                                                  |
|-------------------|----------------------------------------------------------|
| `pet.py`          | the desktop window: watches state, animates              |
| `set_state.py`    | hook target: maps a Claude event → pet state             |
| `install_hooks.py`| adds/removes the hooks in `~/.claude/settings.json`      |
| `config.py`       | shared paths, state list, tool→state map, tunables       |
| `start_pet.bat`   | launches the pet with no console window                  |
