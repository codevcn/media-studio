import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QImage, QKeySequence, QMouseEvent, QPainter, QPen, QPixmap, QShortcut
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
    """Extract one frame through stdout; no temp file and no disk I/O."""
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
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
    selection_changed = Signal(object)
    cursor_changed = Signal(object)

    def __init__(self, image: QImage):
        super().__init__()
        self.source = QPixmap.fromImage(image)
        self.scaled = QPixmap()
        self.image_rect = QRect()
        self.start: QPoint | None = None
        self.end: QPoint | None = None
        self.dragging = False

        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMinimumSize(640, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    @property
    def native_w(self) -> int:
        return self.source.width()

    @property
    def native_h(self) -> int:
        return self.source.height()

    def selection(self) -> tuple[int, int, int, int] | None:
        if self.start is None or self.end is None:
            return None
        x1, x2 = sorted((self.start.x(), self.end.x()))
        y1, y2 = sorted((self.start.y(), self.end.y()))
        return (x1, y1, x2, y2) if x2 > x1 and y2 > y1 else None

    def reset_selection(self) -> None:
        self.start = self.end = None
        self.dragging = False
        self.selection_changed.emit(None)
        self.update()

    def _rescale(self) -> None:
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

    def _to_native(self, p: QPoint, clamp=False) -> QPoint | None:
        if self.image_rect.isNull():
            return None

        if clamp:
            p = QPoint(
                max(self.image_rect.left(), min(self.image_rect.right(), p.x())),
                max(self.image_rect.top(), min(self.image_rect.bottom(), p.y())),
            )
        elif not self.image_rect.contains(p):
            return None

        # Coordinates represent rectangle boundaries, so right/bottom may equal W/H.
        rx = (p.x() - self.image_rect.left()) / max(1, self.image_rect.width() - 1)
        ry = (p.y() - self.image_rect.top()) / max(1, self.image_rect.height() - 1)
        return QPoint(
            max(0, min(self.native_w, round(rx * self.native_w))),
            max(0, min(self.native_h, round(ry * self.native_h))),
        )

    def _to_widget(self, p: QPoint) -> QPoint:
        return QPoint(
            self.image_rect.left() + round((p.x() / self.native_w) * self.image_rect.width()),
            self.image_rect.top() + round((p.y() / self.native_h) * self.image_rect.height()),
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rescale()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        p = self._to_native(event.position().toPoint())
        if p is None:
            return
        self.start = self.end = p
        self.dragging = True
        self.selection_changed.emit(None)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        raw = event.position().toPoint()
        native = self._to_native(raw)
        self.cursor_changed.emit(native)
        if self.dragging:
            self.end = self._to_native(raw, clamp=True)
            self.selection_changed.emit(self.selection())
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton or not self.dragging:
            return
        self.dragging = False
        self.end = self._to_native(event.position().toPoint(), clamp=True)
        self.selection_changed.emit(self.selection())
        self.update()

    def leaveEvent(self, event) -> None:
        if not self.dragging:
            self.cursor_changed.emit(None)
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0b0d10"))
        if not self.scaled.isNull():
            painter.drawPixmap(self.image_rect.topLeft(), self.scaled)

        coords = self.selection()
        if coords:
            x1, y1, x2, y2 = coords
            p1 = self._to_widget(QPoint(x1, y1))
            p2 = self._to_widget(QPoint(x2, y2))
            rect = QRect(p1, p2).normalized()
            painter.fillRect(rect, QColor(0, 229, 255, 45))
            painter.setPen(QPen(QColor("#00e5ff"), 2))
            painter.drawRect(rect)
            painter.setBrush(QColor("#00e5ff"))
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawEllipse(p1, 4, 4)
            painter.drawEllipse(p2, 4, 4)


class LogoLocatorWindow(QMainWindow):
    def __init__(self, video_path: str, timestamp: float, image: QImage):
        super().__init__()
        self.video_path = video_path
        self.final_coords = None

        self.setWindowTitle("MDA · Logo Region Locator")
        self.resize(1180, 820)
        self.setMinimumSize(760, 560)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)

        title = QLabel("Logo Region Locator")
        title.setStyleSheet("font-size:20px;font-weight:700;")
        layout.addWidget(title)

        meta = QLabel(
            f"{Path(video_path).name}  ·  {format_timestamp(timestamp)}  ·  "
            f"{image.width()}×{image.height()} px"
        )
        meta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        meta.setStyleSheet("color:#9aa4ad;")
        layout.addWidget(meta)

        hint = QLabel(
            "Kéo chuột để chọn vùng logo. Tọa độ luôn map về pixel gốc của video. "
            "Enter = xác nhận · R = reset · Ctrl+C = copy."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.canvas = SelectionCanvas(image)
        layout.addWidget(self.canvas, 1)

        info = QHBoxLayout()
        self.cursor_lbl = QLabel("Cursor: —")
        self.p1_lbl = QLabel("P1: —")
        self.p2_lbl = QLabel("P2: —")
        self.size_lbl = QLabel("Size: —")
        for label in (self.cursor_lbl, self.p1_lbl, self.p2_lbl, self.size_lbl):
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info.addWidget(label)
        info.addStretch(1)
        layout.addLayout(info)

        self.coords_lbl = QLabel("Coordinates: —")
        self.coords_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.coords_lbl.setStyleSheet("font-family:Consolas;font-size:15px;font-weight:700;")
        layout.addWidget(self.coords_lbl)

        self.status_lbl = QLabel("Chưa xác nhận")
        self.status_lbl.setStyleSheet("color:#9aa4ad;")
        layout.addWidget(self.status_lbl)

        buttons = QHBoxLayout()
        self.copy_btn = QPushButton("Copy Coordinates")
        self.reset_btn = QPushButton("Reset (R)")
        self.ok_btn = QPushButton("OK (Enter)")
        self.copy_btn.setEnabled(False)
        self.ok_btn.setEnabled(False)
        buttons.addStretch(1)
        buttons.addWidget(self.copy_btn)
        buttons.addWidget(self.reset_btn)
        buttons.addWidget(self.ok_btn)
        layout.addLayout(buttons)

        self.canvas.selection_changed.connect(self._selection_changed)
        self.canvas.cursor_changed.connect(self._cursor_changed)
        self.copy_btn.clicked.connect(self.copy_coordinates)
        self.reset_btn.clicked.connect(self.reset_selection)
        self.ok_btn.clicked.connect(self.confirm_selection)

        self.shortcuts = [
            QShortcut(QKeySequence("Return"), self, activated=self.confirm_selection),
            QShortcut(QKeySequence("Enter"), self, activated=self.confirm_selection),
            QShortcut(QKeySequence("R"), self, activated=self.reset_selection),
            QShortcut(QKeySequence("Ctrl+C"), self, activated=self.copy_coordinates),
        ]

        self.setStyleSheet(
            """
            QMainWindow,QWidget{background:#111418;color:#edf2f7;}
            QPushButton{background:#222831;border:1px solid #3a444f;border-radius:6px;padding:8px 14px;}
            QPushButton:hover{background:#2b333d;}
            QPushButton:disabled{color:#66717c;background:#181c21;}
            """
        )

    def _cursor_changed(self, p: QPoint | None) -> None:
        self.cursor_lbl.setText("Cursor: —" if p is None else f"Cursor: ({p.x()}, {p.y()})")

    def _selection_changed(self, coords) -> None:
        self.status_lbl.setText("Chưa xác nhận")
        self.status_lbl.setStyleSheet("color:#9aa4ad;")
        enabled = coords is not None
        self.copy_btn.setEnabled(enabled)
        self.ok_btn.setEnabled(enabled)

        if not coords:
            self.p1_lbl.setText("P1: —")
            self.p2_lbl.setText("P2: —")
            self.size_lbl.setText("Size: —")
            self.coords_lbl.setText("Coordinates: —")
            return

        x1, y1, x2, y2 = coords
        self.p1_lbl.setText(f"P1: ({x1}, {y1})")
        self.p2_lbl.setText(f"P2: ({x2}, {y2})")
        self.size_lbl.setText(f"Size: {x2-x1}×{y2-y1} px")
        self.coords_lbl.setText(f"Coordinates: {x1},{y1},{x2},{y2}")

    def reset_selection(self) -> None:
        self.final_coords = None
        self.canvas.reset_selection()
        self.status_lbl.setText("Đã reset · kéo chuột để chọn lại")
        self.status_lbl.setStyleSheet("color:#ffcb6b;")

    def copy_coordinates(self) -> None:
        coords = self.canvas.selection()
        if not coords:
            return
        text = ",".join(map(str, coords))
        QApplication.clipboard().setText(text)
        self.status_lbl.setText(f"Đã copy: {text}")
        self.status_lbl.setStyleSheet("color:#7ee787;")

    def confirm_selection(self) -> None:
        coords = self.canvas.selection()
        if not coords:
            self.status_lbl.setText("Hãy chọn vùng logo trước.")
            self.status_lbl.setStyleSheet("color:#ff7b72;")
            return
        self.final_coords = coords
        self.coords_lbl.setText("Coordinates: " + ",".join(map(str, coords)))
        self.status_lbl.setText("✓ Đã xác nhận · có thể copy hoặc đóng cửa sổ")
        self.status_lbl.setStyleSheet("color:#7ee787;")

    def closeEvent(self, event) -> None:
        # Nếu user đã kéo vùng hợp lệ nhưng quên Enter/OK, vẫn log vùng hiện tại.
        self.final_coords = self.canvas.selection()
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
