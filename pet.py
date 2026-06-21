"""The Claude pet: a frameless, translucent, always-on-top desktop critter that
watches ~/.claude/pet/state.json and plays the matching animation.

    python pet.py

Drag it with the mouse to reposition. Right-click for a menu (quit).
"""

import json
import sys
import time

from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPixmap, QAction, QCursor
from PyQt6.QtWidgets import QApplication, QLabel, QMenu, QMessageBox, QWidget, QVBoxLayout

import config


def load_frames(state):
    """Return a list of upscaled QPixmaps for a state, or [] if none found."""
    folder = config.SPRITES_DIR / state
    pixmaps = []
    for path in sorted(folder.glob("frame_*.png")):
        pm = QPixmap(str(path))
        if pm.isNull():
            continue
        pm = pm.scaled(
            pm.width() * config.SCALE,
            pm.height() * config.SCALE,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation,  # nearest-neighbor
        )
        pixmaps.append(pm)
    return pixmaps


class Pet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # keep off the taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Claude Pet")

        self.label = QLabel(self)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        # preload every state's frames; fall back to idle/sleeping if empty
        self.frames = {s: load_frames(s) for s in config.STATES}
        self.state = config.DEFAULT_STATE
        self.frame_i = 0
        self._state_mtime = None
        self._idle_since = None
        self._state_since = time.time()
        self._queue = []  # states waiting for the current one to finish its dwell

        size = self._frame_size()
        self.resize(*size)
        self.place_in_corner()
        self._render()

        self.anim = QTimer(self, timeout=self._tick_frame)
        self.anim.start(config.FRAME_MS)
        self.watch = QTimer(self, timeout=self._poll_state)
        self.watch.start(config.POLL_MS)

        self._drag_offset = None

    # --- helpers -------------------------------------------------------------
    def _frames_for(self, state):
        return self.frames.get(state) or self.frames.get("idle") or []

    def _frame_size(self):
        for s in (self.state, "idle", *config.STATES):
            fr = self.frames.get(s)
            if fr:
                return fr[0].width(), fr[0].height()
        return 24 * config.SCALE, 24 * config.SCALE

    def _render(self):
        frames = self._frames_for(self._visible_state())
        if not frames:
            return
        self.frame_i %= len(frames)
        self.label.setPixmap(frames[self.frame_i])

    def _visible_state(self):
        """Logical idle drifts to 'sleeping' after a while of inactivity."""
        if self.state == "idle" and self._idle_since is not None:
            if time.time() - self._idle_since > config.IDLE_TO_SLEEP_SEC:
                return "sleeping"
        return self.state

    # --- timers --------------------------------------------------------------
    def _tick_frame(self):
        # Promote a queued state first so each one gets at least MIN_DWELL_SEC
        # on screen; if we just switched, show its frame 0 this tick.
        if self._promote_queue():
            return
        self.frame_i += 1
        self._render()

    def _poll_state(self):
        try:
            mtime = config.STATE_FILE.stat().st_mtime
        except OSError:
            return
        if mtime == self._state_mtime:
            return
        self._state_mtime = mtime
        try:
            data = json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        new_state = data.get("state", config.DEFAULT_STATE)
        if new_state not in self.frames:
            new_state = config.DEFAULT_STATE
        self._enqueue(new_state)

    # --- state queue ---------------------------------------------------------
    def _enqueue(self, state):
        """Queue a state, skipping no-op transitions vs. what's already pending."""
        last = self._queue[-1] if self._queue else self.state
        if state == last:
            return
        self._queue.append(state)
        # Bound lag: under sustained churn (PostToolUse stamps "thinking" after
        # every tool), drop the oldest unshown states instead of crawling
        # through a long backlog and falling seconds behind the real session.
        while len(self._queue) > config.MAX_QUEUE:
            del self._queue[0]

    def _promote_queue(self):
        """Apply the next queued state once the current one has had its dwell.

        Returns True if the state changed this tick.
        """
        if not self._queue:
            return False
        if time.time() - self._state_since < config.MIN_DWELL_SEC:
            return False
        self._apply_state(self._queue.pop(0))
        return True

    def _apply_state(self, new_state):
        self.state = new_state
        self.frame_i = 0
        self._state_since = time.time()
        self._idle_since = time.time() if new_state == "idle" else None
        self._render()

    # --- window placement ----------------------------------------------------
    def place_in_corner(self):
        screen = QApplication.primaryScreen().availableGeometry()
        w, h = self.width(), self.height()
        m = config.MARGIN
        corner = config.CORNER
        x = screen.right() - w - m if "right" in corner else screen.left() + m
        y = screen.bottom() - h - m if "bottom" in corner else screen.top() + m
        self.move(x, y)

    # --- interaction ---------------------------------------------------------
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = e.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, e):
        if self._drag_offset is not None:
            self.move(e.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, e):
        self._drag_offset = None

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        snap = QAction("Snap to corner", self)
        snap.triggered.connect(self.place_in_corner)
        menu.addAction(snap)
        quit_act = QAction("Quit pet", self)
        quit_act.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_act)
        menu.exec(QCursor.pos())


def _run_install():
    import install_hooks
    from pathlib import Path

    if getattr(sys, 'frozen', False) and "--uninstall" not in sys.argv:
        set_state = Path(sys.executable).parent / "set_state.exe"
        if not set_state.exists():
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None, "Claude Pet",
                f"set_state.exe not found next to pet.exe.\nExpected: {set_state}",
            )
            sys.exit(1)

    install_hooks.main()
    app = QApplication(sys.argv)
    if "--uninstall" in sys.argv:
        QMessageBox.information(None, "Claude Pet", "Hooks removed from ~/.claude/settings.json.")
    else:
        QMessageBox.information(
            None, "Claude Pet",
            "Hooks installed in ~/.claude/settings.json.\n\n"
            "Restart any open Claude Code sessions to apply.",
        )
    sys.exit(0)


def main():
    if "--install" in sys.argv or "--uninstall" in sys.argv:
        _run_install()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    pet = Pet()
    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
