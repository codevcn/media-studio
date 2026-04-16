import sys
import os
import cv2
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QScrollArea,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QSlider,
    QLabel,
    QSizePolicy,
    QFrame,
)
from PySide6.QtCore import QUrl, Qt, QTimer
from PySide6.QtGui import (
    QShortcut,
    QKeySequence,
    QPixmap,
    QImage,
    QColor,
    QPainter,
    QFont,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


# ---------------------------------------------------------------------------
# Đường dẫn cố định cho thư mục media
# ---------------------------------------------------------------------------
def _get_project_root() -> Path:
    """src/apps/video-player/video_player.py → project_root"""
    return Path(__file__).resolve().parent.parent.parent.parent


PROJECT_ROOT = _get_project_root()
INPUT_DIR = PROJECT_ROOT / "src" / "data" / "media" / "input"
OUTPUT_DIR = PROJECT_ROOT / "src" / "data" / "media" / "output"

INITIAL_INPUT_VIDEO_FILEPATH = {
    "input": str(INPUT_DIR / "input_video.mp4"),
    "output": str(OUTPUT_DIR / "output_video.mp4"),
}

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"}

# ---------------------------------------------------------------------------
# Phím tắt data
# ---------------------------------------------------------------------------
SHORTCUTS_DATA = [
    (
        "PHÁT VIDEO",
        [
            ("Space", "Phát / Tạm dừng"),
            ("Ctrl + Space", "Reset về đầu"),
            ("← (Arrow Left)", "Tua lùi 5 giây"),
            ("→ (Arrow Right)", "Tua tới 5 giây"),
        ],
    ),
    (
        "ÂM LƯỢNG",
        [
            ("↑ (Arrow Up)", "Tăng âm lượng (+2)"),
            ("↓ (Arrow Down)", "Giảm âm lượng (-2)"),
        ],
    ),
    (
        "NGUỒN AUDIO",
        [
            ("Ctrl + ,", "Option 1: chỉ nghe audio video Trái"),
            ("Ctrl + .", "Option 2: chỉ nghe audio video Phải"),
            ("Ctrl + M", "Option 3: toggle Mute / Unmute cả 2 video"),
        ],
    ),
    (
        "MỞ FILE",
        [
            ("Ctrl + [", "Chọn video bên Trái"),
            ("Ctrl + ]", "Chọn video bên Phải"),
        ],
    ),
    (
        "CỬA SỔ",
        [
            ("Ctrl + +  /  Ctrl + =", "Bật / Tắt toàn màn hình"),
            ("Ctrl + K", "Mở bảng phím tắt này"),
            ("Ctrl + Q", "Thoát ứng dụng"),
        ],
    ),
    (
        "BẢNG PHÍM TẮT",
        [
            ("Ctrl + Q", "Đóng bảng phím tắt này"),
        ],
    ),
]


# ===========================================================
# Helpers: extract thumbnail từ video
# ===========================================================
def extract_thumbnail(video_path: str, width: int = 220, height: int = 120) -> QPixmap:
    """
    Lấy frame đầu tiên của video làm thumbnail bằng OpenCV.
    Trả về QPixmap placeholder nếu thất bại.
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            # Thử lấy frame ở giây thứ 1 cho đẹp hơn
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            target_frame = min(int(fps), total_frames - 1) if total_frames > 0 else 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qimg = QImage(
                    frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
                )
                pixmap = QPixmap.fromImage(qimg)
                return pixmap.scaled(
                    width,
                    height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
    except Exception:
        pass
    # Placeholder
    return _make_placeholder_pixmap(width, height)


def _make_placeholder_pixmap(width: int, height: int) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#1e1e2d"))
    painter = QPainter(pixmap)
    painter.setPen(QColor("#3a3a4a"))
    painter.setFont(QFont("Consolas", 11))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🎬")
    painter.end()
    return pixmap


# ===========================================================
# Widget: Một card cặp video trong sidebar
# ===========================================================
class VideoPairCard(QFrame):
    """Card hiển thị 1 cặp video (input + output): thumbnail + tên."""

    STYLE_NORMAL = """
        QFrame#pair_card {
            background-color: #16162a;
            border: 1px solid #2a2a3a;
            border-radius: 8px;
        }
        QFrame#pair_card:hover {
            background-color: #1e1e36;
            border: 1px solid #25f4ee;
        }
    """
    STYLE_SELECTED = """
        QFrame#pair_card {
            background-color: #0f2a2a;
            border: 2px solid #25f4ee;
            border-radius: 8px;
        }
    """

    def __init__(self, input_path: str | None, output_path: str | None, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self._selected = False
        self._callback = None

        self.setObjectName("pair_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self.STYLE_NORMAL)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # --- Thumbnails row ---
        thumb_row = QHBoxLayout()
        thumb_row.setSpacing(4)

        thumb_w, thumb_h = 100, 62

        lbl_left_thumb = QLabel()
        lbl_left_thumb.setFixedSize(thumb_w, thumb_h)
        lbl_left_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_left_thumb.setStyleSheet("border-radius: 4px; background: #0a0a0f;")
        if input_path and os.path.exists(input_path):
            px = extract_thumbnail(input_path, thumb_w, thumb_h)
        else:
            px = _make_placeholder_pixmap(thumb_w, thumb_h)
        lbl_left_thumb.setPixmap(px)

        lbl_right_thumb = QLabel()
        lbl_right_thumb.setFixedSize(thumb_w, thumb_h)
        lbl_right_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_right_thumb.setStyleSheet("border-radius: 4px; background: #0a0a0f;")
        if output_path and os.path.exists(output_path):
            px2 = extract_thumbnail(output_path, thumb_w, thumb_h)
        else:
            px2 = _make_placeholder_pixmap(thumb_w, thumb_h)
        lbl_right_thumb.setPixmap(px2)

        thumb_row.addWidget(lbl_left_thumb)
        thumb_row.addWidget(lbl_right_thumb)
        layout.addLayout(thumb_row)

        # --- Labels row ---
        label_row = QHBoxLayout()
        label_row.setSpacing(4)

        def _name_label(path: str | None, color: str) -> QLabel:
            name = Path(path).stem if path else "—"
            if len(name) > 14:
                name = name[:12] + "…"
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(thumb_w)
            lbl.setStyleSheet(
                f"font-size: 10px; color: {color}; background: transparent;"
            )
            lbl.setToolTip(Path(path).name if path else "")
            return lbl

        label_row.addWidget(_name_label(input_path, "#88ddff"))
        label_row.addWidget(_name_label(output_path, "#aaffcc"))
        layout.addLayout(label_row)

        # Tag nhỏ
        tag_row = QHBoxLayout()
        tag_row.setSpacing(4)

        def _tag(text, color):
            t = QLabel(text)
            t.setFixedWidth(thumb_w)
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            t.setStyleSheet(f"font-size: 9px; color: {color}; background: transparent;")
            return t

        tag_row.addWidget(_tag("◄ Input", "#25f4ee"))
        tag_row.addWidget(_tag("Output ►", "#fe2c55"))
        layout.addLayout(tag_row)

    def set_callback(self, fn):
        self._callback = fn

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setStyleSheet(self.STYLE_SELECTED if selected else self.STYLE_NORMAL)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._callback:
            self._callback(self)
        super().mousePressEvent(event)


# ===========================================================
# Widget: Sidebar danh sách video
# ===========================================================
class VideoListSidebar(QWidget):
    """Sidebar bên phải: quét input/output, hiển thị cặp video, cuộn được."""

    SIDEBAR_WIDTH = 248

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(self.SIDEBAR_WIDTH)
        self._cards: list[VideoPairCard] = []
        self._selected_card: VideoPairCard | None = None
        self._on_pair_selected = None  # callback(input_path, output_path)

        self.setStyleSheet(
            """
            QWidget {
                background-color: #0f0f1a;
            }
            QLabel#sidebar_title {
                font-size: 12px;
                font-weight: bold;
                color: #25f4ee;
                letter-spacing: 1px;
                padding: 10px 10px 6px 10px;
                background: transparent;
            }
            QLabel#sidebar_count {
                font-size: 10px;
                color: #666;
                padding: 0 10px 8px 10px;
                background: transparent;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #0f0f1a;
                width: 5px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: #2a2a3a;
                border-radius: 2px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #25f4ee;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QPushButton#refresh_btn {
                background-color: #1a1a2e;
                border: 1px solid #2a2a3a;
                border-radius: 4px;
                color: #666;
                font-size: 10px;
                padding: 4px 8px;
                margin: 0 10px 8px 10px;
            }
            QPushButton#refresh_btn:hover {
                background-color: #25f4ee;
                color: #0a0a0f;
                border-color: #25f4ee;
            }
        """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Divider trái
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet("color: #2a2a3a;")

        # Header
        self.lbl_title = QLabel("📂  DANH SÁCH VIDEO")
        self.lbl_title.setObjectName("sidebar_title")
        outer.addWidget(self.lbl_title)

        self.lbl_count = QLabel("Đang quét thư mục…")
        self.lbl_count.setObjectName("sidebar_count")
        outer.addWidget(self.lbl_count)

        # Refresh btn
        btn_refresh = QPushButton("⟳  Làm mới")
        btn_refresh.setObjectName("refresh_btn")
        btn_refresh.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_refresh.clicked.connect(self.refresh)
        outer.addWidget(btn_refresh)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 0, 8, 8)
        self._content_layout.setSpacing(6)
        self._content_layout.addStretch()

        self._scroll.setWidget(self._content)
        outer.addWidget(self._scroll, 1)

        # Quét thư mục khi khởi tạo
        QTimer.singleShot(100, self.refresh)

    def set_on_pair_selected(self, fn):
        """fn(input_path: str | None, output_path: str | None)"""
        self._on_pair_selected = fn

    def refresh(self):
        """Quét lại input/output dir và render lại danh sách."""
        # Xóa cũ
        for card in self._cards:
            card.setParent(None)
        self._cards.clear()
        self._selected_card = None

        # Xóa tất cả widget trong layout (trừ stretch cuối)
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        pairs = self._scan_pairs()

        for inp, out in pairs:
            card = VideoPairCard(inp, out)
            card.set_callback(self._card_clicked)
            self._content_layout.insertWidget(self._content_layout.count() - 1, card)
            self._cards.append(card)

        count = len(pairs)
        if count == 0:
            self.lbl_count.setText("Không tìm thấy video nào")
        else:
            self.lbl_count.setText(f"{count} cặp video")

    def select_first(self):
        """Tự động chọn và load cặp video đầu tiên trong danh sách (nếu có)."""
        if self._cards:
            self._card_clicked(self._cards[0])

    def _scan_pairs(self) -> list[tuple[str | None, str | None]]:
        """
        Ghép cặp video từ INPUT_DIR và OUTPUT_DIR theo thứ tự sắp xếp (index).
        File thứ N trong input ghép với file thứ N trong output.
        Trả về list[(input_path, output_path)].
        """

        def _list_videos(folder: Path) -> list[str]:
            if not folder.exists():
                return []
            return sorted(
                str(f)
                for f in folder.iterdir()
                if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
            )

        input_videos = _list_videos(INPUT_DIR)
        output_videos = _list_videos(OUTPUT_DIR)

        # Ghép theo index: input[0]↔output[0], input[1]↔output[1], …
        count = max(len(input_videos), len(output_videos))
        pairs = []
        for i in range(count):
            inp = input_videos[i] if i < len(input_videos) else None
            out = output_videos[i] if i < len(output_videos) else None
            pairs.append((inp, out))

        return pairs

    def _card_clicked(self, card: VideoPairCard):
        # Bỏ chọn card cũ
        if self._selected_card:
            self._selected_card.set_selected(False)
        card.set_selected(True)
        self._selected_card = card

        if self._on_pair_selected:
            self._on_pair_selected(card.input_path, card.output_path)


# ===========================================================
# Dialog: Danh sách phím tắt
# ===========================================================
class ShortcutsDialog(QDialog):
    """Popup hiển thị danh sách toàn bộ phím tắt của ứng dụng."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⌨  Phím tắt")
        self.setFixedWidth(520)
        self.setModal(False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        self.setStyleSheet(
            """
            QDialog {
                background-color: #1a1a24;
                border: 1px solid #2a2a3a;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #25f4ee;
                padding-bottom: 4px;
            }
            QLabel#hint {
                font-size: 12px;
                color: #666;
                padding-bottom: 10px;
            }
            QLabel#group {
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                color: #fe2c55;
                padding-top: 12px;
                padding-bottom: 4px;
            }
            QLabel#key {
                font-size: 13px;
                font-family: Consolas, monospace;
                background-color: #2a2a3a;
                color: #f0eee8;
                border: 1px solid #3a3a4a;
                border-radius: 4px;
                padding: 7px 10px;
                min-width: 160px;
                min-height: 30px;
            }
            QLabel#desc {
                font-size: 13px;
                color: #cccccc;
                padding: 7px 0px 7px 12px;
                min-height: 30px;
            }
            QPushButton#close_btn {
                background-color: #2a2a3a;
                border: 1px solid #3a3a4a;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: bold;
                color: #f0eee8;
                margin-top: 12px;
            }
            QPushButton#close_btn:hover {
                background-color: #fe2c55;
                border-color: #fe2c55;
                color: white;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #1a1a24;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #3a3a4a;
                border-radius: 3px;
            }
        """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(0)

        title = QLabel("⌨  Phím tắt")
        title.setObjectName("title")
        outer.addWidget(title)

        hint = QLabel("Nhấn  Q  để đóng  •  Nhấn  Ctrl+K  để mở lại")
        hint.setObjectName("hint")
        outer.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 4, 10, 8)
        content_layout.setSpacing(0)

        for idx, (group_name, shortcuts) in enumerate(SHORTCUTS_DATA):
            if idx > 0:
                content_layout.addSpacing(14)

            group_label = QLabel(group_name)
            group_label.setObjectName("group")
            content_layout.addWidget(group_label)
            content_layout.addSpacing(4)

            for key, description in shortcuts:
                row = QHBoxLayout()
                row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(0)

                key_label = QLabel(key)
                key_label.setObjectName("key")
                key_label.setFixedWidth(200)
                key_label.setAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                )

                desc_label = QLabel(description)
                desc_label.setObjectName("desc")
                desc_label.setWordWrap(True)
                desc_label.setAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                )

                row.addWidget(key_label)
                row.addWidget(desc_label, 1)
                content_layout.addLayout(row)
                content_layout.addSpacing(4)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        outer.addWidget(scroll)

        close_btn = QPushButton("Đóng (Ctrl+Q)")
        close_btn.setObjectName("close_btn")
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_btn.clicked.connect(self.hide)
        outer.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.hide)

        self.adjustSize()
        max_h = 560
        if self.height() > max_h:
            self.setFixedHeight(max_h)


# ===========================================================
# Main Window
# ===========================================================
class DualVideoPlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trình phát Video Kép (Hỗ trợ Phím tắt)")
        self.resize(1440, 760)

        self.setStyleSheet(
            """
            QWidget {
                background-color: #121212;
                color: white;
            }
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #333333;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #5c5c5c;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
        """
        )

        # ---- Root layout: player area | sidebar ----
        root_widget = QWidget(self)
        self.setCentralWidget(root_widget)
        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---- Player area (left) ----
        player_widget = QWidget()
        main_layout = QVBoxLayout(player_widget)
        main_layout.setContentsMargins(10, 10, 10, 15)

        # 1. Khu vực hiển thị 2 Video
        video_area_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        self.video_widget_left = QVideoWidget()
        self.video_widget_left.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.lbl_left_name = QLabel("—")
        self.lbl_left_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_left_name.setStyleSheet(
            "font-size: 11px; color: #88ddff; background: transparent; padding: 2px 0;"
        )
        self.btn_load_left = QPushButton("Chọn Video Trái")
        left_layout.addWidget(self.video_widget_left)
        left_layout.addWidget(self.btn_load_left)
        video_area_layout.addLayout(left_layout)

        right_layout = QVBoxLayout()
        self.video_widget_right = QVideoWidget()
        self.video_widget_right.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.lbl_right_name = QLabel("—")
        self.lbl_right_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_right_name.setStyleSheet(
            "font-size: 11px; color: #aaffcc; background: transparent; padding: 2px 0;"
        )
        self.btn_load_right = QPushButton("Chọn Video Phải")
        right_layout.addWidget(self.video_widget_right)
        right_layout.addWidget(self.btn_load_right)
        video_area_layout.addLayout(right_layout)

        main_layout.addLayout(video_area_layout, 1)

        self.player_left = QMediaPlayer()
        self.audio_left = QAudioOutput()
        self.player_left.setVideoOutput(self.video_widget_left)
        self.player_left.setAudioOutput(self.audio_left)

        self.player_right = QMediaPlayer()
        self.audio_right = QAudioOutput()
        self.player_right.setVideoOutput(self.video_widget_right)
        self.player_right.setAudioOutput(self.audio_right)

        # 2. Thanh tiến trình
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 0)
        self.progress_slider.setStyleSheet("margin-top: 10px; margin-bottom: 10px;")
        main_layout.addWidget(self.progress_slider)

        # 3. Các nút điều khiển
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_reset = QPushButton("⏮ Về ban đầu")
        self.btn_prev = QPushButton("⏪ -5s")
        self.btn_play_pause = QPushButton("▶ Phát")
        self.btn_next = QPushButton("+5s ⏩")
        self.btn_audio_left = QPushButton("◄ Audio Trái")
        self.btn_audio_right = QPushButton("Audio Phải ►")
        self.btn_mute_all = QPushButton("🔊 Cả 2")

        controls_layout.addWidget(self.btn_reset)
        controls_layout.addWidget(self.btn_prev)
        controls_layout.addWidget(self.btn_play_pause)
        controls_layout.addWidget(self.btn_next)
        controls_layout.addWidget(self.btn_audio_left)
        controls_layout.addWidget(self.btn_audio_right)
        controls_layout.addWidget(self.btn_mute_all)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(120)
        controls_layout.addWidget(self.volume_slider)

        main_layout.addLayout(controls_layout)

        root_layout.addWidget(player_widget, 1)

        # ---- Sidebar (right) ----
        self._sidebar = VideoListSidebar()
        self._sidebar.set_on_pair_selected(self._on_sidebar_pair_selected)
        root_layout.addWidget(self._sidebar)

        # ---- Khởi tạo trạng thái audio ----
        self.change_volume(50)
        self._audio_option = 1
        self._both_muted = False
        self._apply_audio_state()

        # ---- Ngăn chặn Space click vào nút đang focus ----
        self.remove_focus_policy()

        # ---- Phím tắt ----
        self.setup_shortcuts()

        # ---- Kết nối tín hiệu ----
        self.btn_load_left.clicked.connect(
            lambda: self.load_video_dialog(self.player_left, "left")
        )
        self.btn_load_right.clicked.connect(
            lambda: self.load_video_dialog(self.player_right, "right")
        )

        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.btn_reset.clicked.connect(self.reset_videos)
        self.btn_prev.clicked.connect(self.seek_backward)
        self.btn_next.clicked.connect(self.seek_forward)

        self.btn_audio_left.clicked.connect(lambda: self.select_audio_option(1))
        self.btn_audio_right.clicked.connect(lambda: self.select_audio_option(2))
        self.btn_mute_all.clicked.connect(lambda: self.select_audio_option(3))

        self.volume_slider.valueChanged.connect(self.change_volume)
        self.progress_slider.sliderMoved.connect(self.set_position)

        self.player_left.positionChanged.connect(self.update_slider_position)
        self.player_left.durationChanged.connect(self.update_slider_duration)
        self.player_right.positionChanged.connect(self.update_slider_position)
        self.player_right.durationChanged.connect(self.update_slider_duration)

        self.player_left.mediaStatusChanged.connect(
            lambda status: self.on_media_status_changed(self.player_left, status)
        )
        self.player_right.mediaStatusChanged.connect(
            lambda status: self.on_media_status_changed(self.player_right, status)
        )

        # ---- Auto load cặp đầu tiên từ sidebar ----
        # Sidebar đã được QTimer.singleShot(100) để refresh, ta delay thêm để đảm bảo render xong
        QTimer.singleShot(150, self._sidebar.select_first)

        # ---- Shortcuts dialog ----
        self._shortcuts_dialog = ShortcutsDialog(self)
        QTimer.singleShot(200, self.show_shortcuts)

    # ------------------------------------------------------------------
    # Sidebar callback
    # ------------------------------------------------------------------
    def _on_sidebar_pair_selected(
        self, input_path: str | None, output_path: str | None
    ):
        """Load cặp video được chọn từ sidebar vào 2 player."""
        if input_path and os.path.exists(input_path):
            self.player_left.setSource(QUrl.fromLocalFile(input_path))
            self.player_left.pause()
            self.lbl_left_name.setText(Path(input_path).name)
        else:
            self.lbl_left_name.setText("—")

        if output_path and os.path.exists(output_path):
            self.player_right.setSource(QUrl.fromLocalFile(output_path))
            self.player_right.pause()
            self.lbl_right_name.setText(Path(output_path).name)
        else:
            self.lbl_right_name.setText("—")

        # Reset về đầu
        self.player_left.setPosition(0)
        self.player_right.setPosition(0)
        self.btn_play_pause.setText("▶ Phát")

    # ------------------------------------------------------------------

    def remove_focus_policy(self):
        widgets = [
            self.btn_load_left,
            self.btn_load_right,
            self.btn_reset,
            self.btn_prev,
            self.btn_play_pause,
            self.btn_next,
            self.btn_audio_left,
            self.btn_audio_right,
            self.btn_mute_all,
            self.progress_slider,
            self.volume_slider,
        ]
        for widget in widgets:
            widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+["), self).activated.connect(
            lambda: self.load_video_dialog(self.player_left, "left")
        )
        QShortcut(QKeySequence("Ctrl+]"), self).activated.connect(
            lambda: self.load_video_dialog(self.player_right, "right")
        )

        QShortcut(QKeySequence(Qt.Key.Key_Space), self).activated.connect(
            self.toggle_play_pause
        )
        QShortcut(QKeySequence(Qt.Key.Key_Left), self).activated.connect(
            self.seek_backward
        )
        QShortcut(QKeySequence(Qt.Key.Key_Right), self).activated.connect(
            self.seek_forward
        )

        QShortcut(QKeySequence("Ctrl+Space"), self).activated.connect(self.reset_videos)

        QShortcut(QKeySequence("Ctrl+M"), self).activated.connect(
            lambda: self.select_audio_option(3)
        )
        QShortcut(QKeySequence("Ctrl+,"), self).activated.connect(
            lambda: self.select_audio_option(1)
        )
        QShortcut(QKeySequence("Ctrl+."), self).activated.connect(
            lambda: self.select_audio_option(2)
        )

        QShortcut(QKeySequence(Qt.Key.Key_Up), self).activated.connect(
            self.increase_volume
        )
        QShortcut(QKeySequence(Qt.Key.Key_Down), self).activated.connect(
            self.decrease_volume
        )
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(
            self.toggle_fullscreen
        )
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(
            self.toggle_fullscreen
        )

        QShortcut(QKeySequence("Ctrl+K"), self).activated.connect(self.show_shortcuts)
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)

    def show_shortcuts(self):
        self._shortcuts_dialog.show()
        self._shortcuts_dialog.raise_()
        self._shortcuts_dialog.activateWindow()
        main_geo = self.geometry()
        dlg_geo = self._shortcuts_dialog.frameGeometry()
        cx = main_geo.left() + (main_geo.width() - dlg_geo.width()) // 2
        cy = main_geo.top() + (main_geo.height() - dlg_geo.height()) // 2
        self._shortcuts_dialog.move(cx, cy)

    def load_video_dialog(self, player: QMediaPlayer, side: str):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Chọn tệp video")
        file_dialog.setNameFilter("Video Files (*.mp4 *.avi *.mkv *.mov)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]
                player.setSource(QUrl.fromLocalFile(path))
                player.pause()
                if side == "left":
                    self.lbl_left_name.setText(Path(path).name)
                else:
                    self.lbl_right_name.setText(Path(path).name)

    def toggle_play_pause(self):
        state_left = self.player_left.playbackState()
        state_right = self.player_right.playbackState()

        if (
            state_left == QMediaPlayer.PlaybackState.PlayingState
            or state_right == QMediaPlayer.PlaybackState.PlayingState
        ):
            self.player_left.pause()
            self.player_right.pause()
            self.btn_play_pause.setText("▶ Phát")
        else:
            if self.player_left.mediaStatus() == QMediaPlayer.MediaStatus.EndOfMedia:
                self.player_left.setPosition(0)
            if self.player_right.mediaStatus() == QMediaPlayer.MediaStatus.EndOfMedia:
                self.player_right.setPosition(0)

            self.player_left.play()
            self.player_right.play()
            self.btn_play_pause.setText("⏸ Tạm dừng")

    def reset_videos(self):
        self.player_left.setPosition(0)
        self.player_right.setPosition(0)

    def seek_backward(self):
        for player in [self.player_left, self.player_right]:
            current_position = player.position()
            new_position = max(0, current_position - 5000)
            player.setPosition(new_position)

    def seek_forward(self):
        for player in [self.player_left, self.player_right]:
            current_position = player.position()
            duration = player.duration()
            new_position = min(duration, current_position + 5000)
            player.setPosition(new_position)

    # --- Audio styles ---
    _STYLE_AUDIO_ACTIVE = """
        QPushButton {
            background-color: #38bdf8;
            color: #0a0a0f;
            border: 1px solid #0284c7;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #7dd3fc; }
    """
    _STYLE_BOTH_MUTED = """
        QPushButton {
            background-color: #fe2c55;
            color: white;
            border: 1px solid #c0143c;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #ff6b9d; }
    """
    _STYLE_BOTH_UNMUTED = """
        QPushButton {
            background-color: #4ade80;
            color: #0a0a0f;
            border: 1px solid #16a34a;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #86efac; }
    """

    def select_audio_option(self, option: int):
        if option == 3:
            if self._audio_option != 3:
                self._audio_option = 3
                self._both_muted = True
            else:
                self._both_muted = not self._both_muted
        else:
            self._audio_option = option
        self._apply_audio_state()

    def _apply_audio_state(self):
        off = ""
        if self._audio_option == 1:
            self.audio_left.setMuted(False)
            self.audio_right.setMuted(True)
            self.btn_audio_left.setText("◄ Audio Trái")
            self.btn_audio_right.setText("Audio Phải ►")
            self.btn_mute_all.setText("🔊 Cả 2")
            self.btn_audio_left.setStyleSheet(self._STYLE_AUDIO_ACTIVE)
            self.btn_audio_right.setStyleSheet(off)
            self.btn_mute_all.setStyleSheet(off)
        elif self._audio_option == 2:
            self.audio_left.setMuted(True)
            self.audio_right.setMuted(False)
            self.btn_audio_left.setText("◄ Audio Trái")
            self.btn_audio_right.setText("Audio Phải ►")
            self.btn_mute_all.setText("🔊 Cả 2")
            self.btn_audio_left.setStyleSheet(off)
            self.btn_audio_right.setStyleSheet(self._STYLE_AUDIO_ACTIVE)
            self.btn_mute_all.setStyleSheet(off)
        elif self._audio_option == 3:
            self.audio_left.setMuted(self._both_muted)
            self.audio_right.setMuted(self._both_muted)
            self.btn_audio_left.setText("◄ Audio Trái")
            self.btn_audio_right.setText("Audio Phải ►")
            self.btn_audio_left.setStyleSheet(off)
            self.btn_audio_right.setStyleSheet(off)
            if self._both_muted:
                self.btn_mute_all.setText("🔇 Muted")
                self.btn_mute_all.setStyleSheet(self._STYLE_BOTH_MUTED)
            else:
                self.btn_mute_all.setText("🔊 Unmuted")
                self.btn_mute_all.setStyleSheet(self._STYLE_BOTH_UNMUTED)

    def change_volume(self, value):
        volume_level = value / 100.0
        self.audio_left.setVolume(volume_level)
        self.audio_right.setVolume(volume_level)

    def update_slider_duration(self):
        max_duration = max(self.player_left.duration(), self.player_right.duration())
        self.progress_slider.setRange(0, max_duration)

    def update_slider_position(self):
        current_pos = max(self.player_left.position(), self.player_right.position())
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(current_pos)
        self.progress_slider.blockSignals(False)

    def set_position(self, position):
        self.player_left.setPosition(position)
        self.player_right.setPosition(position)

    def on_media_status_changed(self, player, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            player.setPosition(player.duration())
            player.pause()

            if (
                self.player_left.playbackState()
                != QMediaPlayer.PlaybackState.PlayingState
                and self.player_right.playbackState()
                != QMediaPlayer.PlaybackState.PlayingState
            ):
                self.btn_play_pause.setText("▶ Phát")

    def increase_volume(self):
        self.volume_slider.setValue(min(100, self.volume_slider.value() + 2))

    def decrease_volume(self):
        self.volume_slider.setValue(max(0, self.volume_slider.value() - 2))

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DualVideoPlayerWindow()
    window.show()
    sys.exit(app.exec())
