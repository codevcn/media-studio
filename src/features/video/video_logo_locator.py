import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QImage,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def parse_timestamp(value: str) -> float:
    """Support: 15, 15.5, MM:SS, HH:MM:SS(.ms)."""
    value = value.strip()
    if not value:
        raise ValueError("Timestamp không được để trống.")

    try:
        seconds = float(value)
        if seconds < 0:
            raise ValueError("Timestamp phải >= 0.")
        return seconds
    except ValueError:
        pass

    parts = value.split(":")
    if len(parts) not in (2, 3):
        raise ValueError("Timestamp phải là giây, MM:SS hoặc HH:MM:SS(.ms).")

    try:
        if len(parts) == 2:
            hours, minutes, seconds = 0, int(parts[0]), float(parts[1])
        else:
            hours, minutes, seconds = int(parts[0]), int(parts[1]), float(parts[2])
    except ValueError as exc:
        raise ValueError("Timestamp phải là giây, MM:SS hoặc HH:MM:SS(.ms).") from exc

    if hours < 0 or minutes < 0 or seconds < 0:
        raise ValueError("Timestamp phải >= 0.")
    if minutes >= 60 or seconds >= 60:
        raise ValueError("Với timestamp có ':', phút và giây phải < 60.")

    return hours * 3600 + minutes * 60 + seconds


def format_timestamp(seconds: float) -> str:
    total_ms = round(seconds * 1000)
    h, rem = divmod(total_ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}" + (f".{ms:03d}" if ms else "")


def extract_frame(video_path: str, timestamp: float) -> QImage:
    """
    Extract exactly one frame through stdout.

    The frame never touches disk: FFmpeg -> stdout -> QImage.
    """
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{timestamp:.6f}",
        "-i",
        video_path,
        "-map",
        "0:v:0",
        "-frames:v",
        "1",
        "-f",
        "image2pipe",
        "-vcodec",
        "png",
        "pipe:1",
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Không tìm thấy FFmpeg trong PATH.") from exc

    if result.returncode != 0 or not result.stdout:
        error = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(error or "Không lấy được frame tại timestamp đã chọn.")

    image = QImage.fromData(result.stdout, "PNG")
    if image.isNull():
        raise RuntimeError("Qt không thể giải mã frame do FFmpeg trả về.")

    return image


class SelectionCanvas(QWidget):
    """
    Image canvas using native-video coordinates.

    Selection workflow:
      - Left click #1 -> P1
      - Move mouse     -> live rectangle preview
      - Left click #2 -> P2 / finalize rectangle
      - Another click -> immediately starts a new selection

    The image can be scaled to fit the window, but all returned coordinates
    always refer to the original frame resolution.
    """

    selection_changed = Signal(object)
    cursor_changed = Signal(object)

    def __init__(self, image: QImage):
        super().__init__()

        self.source = QPixmap.fromImage(image)
        self.scaled = QPixmap()
        self.image_rect = QRect()

        # Native-image coordinates. P2 is None while waiting for click #2.
        self.start: QPoint | None = None
        self.end: QPoint | None = None
        self.hover: QPoint | None = None
        self.waiting_for_second_click = False

        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMinimumSize(480, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    @property
    def native_w(self) -> int:
        return self.source.width()

    @property
    def native_h(self) -> int:
        return self.source.height()

    @staticmethod
    def _normalize_points(p1: QPoint, p2: QPoint) -> tuple[int, int, int, int] | None:
        x1, x2 = sorted((p1.x(), p2.x()))
        y1, y2 = sorted((p1.y(), p2.y()))
        if x2 <= x1 or y2 <= y1:
            return None
        return x1, y1, x2, y2

    def selection(self) -> tuple[int, int, int, int] | None:
        """Return the finalized P1/P2 rectangle, or None."""
        if self.start is None or self.end is None:
            return None
        return self._normalize_points(self.start, self.end)

    def preview_selection(self) -> tuple[int, int, int, int] | None:
        """Return final selection, or P1 -> current cursor while waiting for P2."""
        if self.start is None:
            return None

        target = self.end if self.end is not None else self.hover
        if target is None:
            return None

        return self._normalize_points(self.start, target)

    def reset_selection(self) -> None:
        self.start = None
        self.end = None
        self.hover = None
        self.waiting_for_second_click = False
        self.selection_changed.emit(None)
        self.update()

    def _rescale(self) -> None:
        """Scale only when the widget changes size, not on every mouse move."""
        if self.width() < 2 or self.height() < 2:
            return

        self.scaled = self.source.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        left = (self.width() - self.scaled.width()) // 2
        top = (self.height() - self.scaled.height()) // 2
        self.image_rect = QRect(left, top, self.scaled.width(), self.scaled.height())
        self.update()

    def _to_native(self, p: QPoint, clamp: bool = False) -> QPoint | None:
        if self.image_rect.isNull():
            return None

        if clamp:
            p = QPoint(
                max(self.image_rect.left(), min(self.image_rect.right(), p.x())),
                max(self.image_rect.top(), min(self.image_rect.bottom(), p.y())),
            )
        elif not self.image_rect.contains(p):
            return None

        # Coordinates are rectangle boundaries, therefore x2/y2 may equal W/H.
        rx = (p.x() - self.image_rect.left()) / max(1, self.image_rect.width() - 1)
        ry = (p.y() - self.image_rect.top()) / max(1, self.image_rect.height() - 1)

        return QPoint(
            max(0, min(self.native_w, round(rx * self.native_w))),
            max(0, min(self.native_h, round(ry * self.native_h))),
        )

    def _to_widget(self, p: QPoint) -> QPoint:
        """Map native rectangle-boundary coordinates back to the fitted image."""
        return QPoint(
            self.image_rect.left()
            + round((p.x() / max(1, self.native_w)) * self.image_rect.width()),
            self.image_rect.top()
            + round((p.y() / max(1, self.native_h)) * self.image_rect.height()),
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rescale()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        point = self._to_native(event.position().toPoint())
        if point is None:
            return

        # No selection yet OR a complete selection already exists:
        # this click becomes the new P1.
        if self.start is None or self.end is not None:
            self.start = point
            self.end = None
            self.hover = point
            self.waiting_for_second_click = True
            self.selection_changed.emit(None)
            self.update()
            return

        # P1 already exists -> this is click #2 / P2.
        if self.waiting_for_second_click:
            candidate = self._normalize_points(self.start, point)

            # Same X or same Y would create a zero-area rectangle.
            # Keep P1 and continue waiting for a valid P2.
            if candidate is None:
                self.hover = point
                self.selection_changed.emit(None)
                self.update()
                return

            self.end = point
            self.hover = point
            self.waiting_for_second_click = False
            self.selection_changed.emit(candidate)
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        raw = event.position().toPoint()
        native = self._to_native(raw)
        self.cursor_changed.emit(native)

        # Only repaint the overlay while choosing P2.
        # The expensive image scaling is cached and untouched here.
        if (
            self.waiting_for_second_click
            and self.start is not None
            and native is not None
        ):
            self.hover = native
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        # Deliberately do nothing: selection is click-click, not drag-release.
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event) -> None:
        self.cursor_changed.emit(None)
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0b0d10"))

        if not self.scaled.isNull():
            painter.drawPixmap(self.image_rect.topLeft(), self.scaled)

        # Always show P1 once it exists.
        if self.start is not None:
            p1 = self._to_widget(self.start)
            painter.setBrush(QColor("#00e5ff"))
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawEllipse(p1, 4, 4)

        coords = self.preview_selection()
        if not coords:
            return

        x1, y1, x2, y2 = coords
        p1 = self._to_widget(QPoint(x1, y1))
        p2 = self._to_widget(QPoint(x2, y2))
        rect = QRect(p1, p2).normalized()

        pen = QPen(QColor("#00e5ff"), 2)
        if self.waiting_for_second_click:
            pen.setStyle(Qt.PenStyle.DashLine)

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

        painter.setBrush(QColor("#00e5ff"))
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawEllipse(p1, 4, 4)
        painter.drawEllipse(p2, 4, 4)


class LogoLocatorWindow(QMainWindow):
    def __init__(self, video_path: str, timestamp: float, image: QImage):
        super().__init__()

        self.video_path = video_path
        self.final_coords: tuple[int, int, int, int] | None = None

        self.setWindowTitle("MDA · Logo Region Locator")
        self.resize(1180, 860)
        self.setMinimumSize(760, 480)

        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # ------------------------------------------------------------------
        # Compact header: use horizontal space instead of consuming height.
        # ------------------------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(18)

        header_left = QVBoxLayout()
        header_left.setContentsMargins(0, 0, 0, 0)
        header_left.setSpacing(1)

        title = QLabel("Logo Region Locator")
        title.setStyleSheet("font-size:18px;font-weight:700;")

        meta = QLabel(
            f"{Path(video_path).name}  ·  {format_timestamp(timestamp)}  ·  "
            f"{image.width()}×{image.height()} px"
        )
        meta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        meta.setStyleSheet("font-size:12px;color:#9aa4ad;")

        header_left.addWidget(title)
        header_left.addWidget(meta)

        header_right = QVBoxLayout()
        header_right.setContentsMargins(0, 0, 0, 0)
        header_right.setSpacing(1)

        hint = QLabel(
            "Click 1 = P1  ·  Click 2 = P2  ·  Enter = confirm  ·  "
            "R = reset  ·  Ctrl+C = copy"
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        hint.setStyleSheet("font-size:12px;color:#d9e1e8;")

        self.status_lbl = QLabel("Chọn điểm P1 trên frame.")
        self.status_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.status_lbl.setStyleSheet("font-size:12px;color:#9aa4ad;")

        header_right.addWidget(hint)
        header_right.addWidget(self.status_lbl)

        header.addLayout(header_left, 0)
        header.addStretch(1)
        header.addLayout(header_right, 0)
        layout.addLayout(header)

        # ------------------------------------------------------------------
        # Main canvas gets every remaining vertical pixel.
        # ------------------------------------------------------------------
        self.canvas = SelectionCanvas(image)
        layout.addWidget(self.canvas, 1)

        # ------------------------------------------------------------------
        # Compact single-row footer.
        # ------------------------------------------------------------------
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(10)

        self.info_lbl = QLabel("Cursor: —  ·  P1: —  ·  P2: —  ·  Size: —")
        self.info_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.info_lbl.setStyleSheet("font-size:12px;color:#cbd5df;")

        self.coords_lbl = QLabel("Coordinates: —")
        self.coords_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.coords_lbl.setStyleSheet(
            "font-family:Consolas;font-size:13px;font-weight:700;color:#edf2f7;"
        )

        self.copy_btn = QPushButton("Copy Coordinates")
        self.reset_btn = QPushButton("Reset (R)")
        self.ok_btn = QPushButton("OK (Enter)")

        self.copy_btn.setEnabled(False)
        self.ok_btn.setEnabled(False)

        footer.addWidget(self.info_lbl, 0)
        footer.addWidget(self.coords_lbl, 0)
        footer.addStretch(1)
        footer.addWidget(self.copy_btn)
        footer.addWidget(self.reset_btn)
        footer.addWidget(self.ok_btn)
        layout.addLayout(footer)

        # Signals.
        self.canvas.selection_changed.connect(self._selection_changed)
        self.canvas.cursor_changed.connect(self._cursor_changed)
        self.copy_btn.clicked.connect(self.copy_coordinates)
        self.reset_btn.clicked.connect(self.reset_selection)
        self.ok_btn.clicked.connect(self.confirm_selection)

        # Keyboard shortcuts work while focus is anywhere inside this window.
        self.shortcuts = [
            QShortcut(QKeySequence("Return"), self, activated=self.confirm_selection),
            QShortcut(QKeySequence("Enter"), self, activated=self.confirm_selection),
            QShortcut(QKeySequence("R"), self, activated=self.reset_selection),
            QShortcut(QKeySequence("Escape"), self, activated=self.reset_selection),
            QShortcut(QKeySequence("Ctrl+C"), self, activated=self.copy_coordinates),
        ]

        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #111418;
                color: #edf2f7;
            }
            QPushButton {
                background: #222831;
                border: 1px solid #3a444f;
                border-radius: 6px;
                padding: 6px 11px;
                min-height: 28px;
            }
            QPushButton:hover {
                background: #2b333d;
            }
            QPushButton:pressed {
                background: #343e49;
            }
            QPushButton:disabled {
                color: #66717c;
                background: #181c21;
            }
            """)

    def _refresh_info_label(self, cursor: QPoint | None = None) -> None:
        if cursor is None:
            cursor_text = "—"
        else:
            cursor_text = f"({cursor.x()}, {cursor.y()})"

        start = self.canvas.start
        coords = self.canvas.selection()

        if coords:
            # Show normalized corners so the labels match rm-logo output exactly.
            x1, y1, x2, y2 = coords
            p1_text = f"({x1}, {y1})"
            p2_text = f"({x2}, {y2})"
            size_text = f"{x2 - x1}×{y2 - y1} px"
        else:
            p1_text = "—" if start is None else f"({start.x()}, {start.y()})"
            p2_text = "—"
            size_text = "—"

        self.info_lbl.setText(
            f"Cursor: {cursor_text}  ·  P1: {p1_text}  ·  "
            f"P2: {p2_text}  ·  Size: {size_text}"
        )

    def _cursor_changed(self, point: QPoint | None) -> None:
        self._refresh_info_label(point)

    def _selection_changed(self, coords) -> None:
        # Any new/changed selection invalidates the previous explicit confirm.
        self.final_coords = None
        self._refresh_info_label(None)

        if coords is None:
            self.copy_btn.setEnabled(False)
            self.ok_btn.setEnabled(False)
            self.coords_lbl.setText("Coordinates: —")

            if self.canvas.start is not None and self.canvas.end is None:
                self.status_lbl.setText("P1 đã chọn · click lần 2 để đặt P2.")
                self.status_lbl.setStyleSheet("font-size:12px;color:#ffcb6b;")
            else:
                self.status_lbl.setText("Chọn điểm P1 trên frame.")
                self.status_lbl.setStyleSheet("font-size:12px;color:#9aa4ad;")
            return

        x1, y1, x2, y2 = coords
        self.coords_lbl.setText(f"Coordinates: {x1},{y1},{x2},{y2}")
        self.copy_btn.setEnabled(True)
        self.ok_btn.setEnabled(True)
        self.status_lbl.setText("Đã chọn P1 + P2 · Enter/OK để xác nhận.")
        self.status_lbl.setStyleSheet("font-size:12px;color:#7dd3fc;")

    def reset_selection(self) -> None:
        self.final_coords = None
        self.canvas.reset_selection()
        self.coords_lbl.setText("Coordinates: —")
        self.status_lbl.setText("Đã reset · click để chọn P1 mới.")
        self.status_lbl.setStyleSheet("font-size:12px;color:#ffcb6b;")
        self._refresh_info_label(None)

    def copy_coordinates(self) -> None:
        coords = self.canvas.selection()
        if not coords:
            self.status_lbl.setText("Hãy chọn đủ P1 và P2 trước.")
            self.status_lbl.setStyleSheet("font-size:12px;color:#ff7b72;")
            return

        text = ",".join(map(str, coords))
        QApplication.clipboard().setText(text)
        self.status_lbl.setText(f"Đã copy: {text}")
        self.status_lbl.setStyleSheet("font-size:12px;color:#7ee787;")

    def confirm_selection(self) -> None:
        coords = self.canvas.selection()
        if not coords:
            if self.canvas.start is not None:
                self.status_lbl.setText("Đã có P1 · hãy click lần 2 để chọn P2.")
            else:
                self.status_lbl.setText("Hãy click lần 1 để chọn P1 trước.")
            self.status_lbl.setStyleSheet("font-size:12px;color:#ff7b72;")
            return

        self.final_coords = coords
        self.coords_lbl.setText("Coordinates: " + ",".join(map(str, coords)))
        self.status_lbl.setText("✓ Đã xác nhận · có thể copy hoặc đóng cửa sổ.")
        self.status_lbl.setStyleSheet("font-size:12px;color:#7ee787;")

    def closeEvent(self, event) -> None:
        # If the user selected a valid rectangle but forgot Enter/OK,
        # still return the current coordinates to the console.
        current = self.canvas.selection()
        if current is not None:
            self.final_coords = current
        event.accept()


def run_locator(video_path: str, timestamp: float) -> int:
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Không tìm thấy video: {video_path}")

    app = QApplication.instance() or QApplication(sys.argv[:1])

    image = extract_frame(video_path, timestamp)
    window = LogoLocatorWindow(video_path, timestamp, image)
    window.show()
    app.exec()

    if not window.final_coords:
        print("\nNo logo region selected.")
        return 1

    coords = ",".join(map(str, window.final_coords))
    print("\nLogo region:")
    print(coords)
    print("\nRun:")
    print(f'mda video rm-logo "{video_path}" "{coords}"')
    return 0


def main() -> int:
    if len(sys.argv) != 3:
        print("Sử dụng: video_logo_locator.py <video_path> <timestamp>")
        return 2

    video_path = os.path.abspath(os.path.expanduser(sys.argv[1]))

    try:
        return run_locator(video_path, parse_timestamp(sys.argv[2]))
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f">>> Error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
