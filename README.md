# Media Studio CLI (mda)

Media Studio là bộ công cụ CLI và GUI cá nhân để xử lý video, âm thanh, hình ảnh, media file và tải nội dung đa nền tảng.

## Tính Năng

### Chế Độ Tương Tác & Auto-Complete (Interactive REPL)

- `mda` (không kèm tham số): Khởi động chế độ tương tác `mda > `.
- Nhấn **`[Tab]`** để tự động hoàn thành / xoay vòng danh sách `Type` (A-Z) và `Action`.
- Hỗ trợ lọc theo tiền tố, bảo toàn tham số phụ khi đổi action, và các lệnh nội bộ: `help`, `types`, `clear`, `exit`.

### App

- `mda app player`: mở trình phát video kép bằng PySide6 để so sánh hai video song song.
- App video player quét danh sách video theo cặp input/output và hỗ trợ phím tắt, tua, chỉnh âm lượng, chọn nguồn audio.

### Video

- `mda video rm-logo <input_path> <x,y,w,h> [output_path]`: xóa watermark/logo bằng FFmpeg `delogo`.
- `mda video frames <input_path> <gap_time> [limit]`: trích xuất frame PNG theo khoảng thời gian, ví dụ `5s`, `200ms`, `2m`.

### Audio

- `mda audio extract <input_path> <output_path>`: tách âm thanh từ video sang `.wav` hoặc `.mp3`.

### Image

- `mda image flip <input_path> <horizontal|vertical> [output_path]`: lật ảnh ngang hoặc dọc bằng Pillow.

### Media

- `mda media slice <input_path> <start-end> [output_filename]`: cắt một đoạn audio/video, ví dụ `00:10-01:22`.
- `mda media part-size <input_path> <size_mb> [limit]`: chia file media theo dung lượng mục tiêu.
- `mda media part-time <input_path> <duration> [limit]`: chia file media theo thời lượng, ví dụ `20s`, `3m`, `3p`.

### Downloader

- `mda dld <platform> <url> [option] [--filename] [--folder] [--format] [--threads] [--cookies | --cookies-from-browser]`
- Các platform dùng `yt-dlp` + `aria2c`: `ytb`, `ytb-music`, `fb`, `insta`, `tiktok`, `bilibili`, `bili`, `bilili`, `soundcloud`.
- `spotify` dùng `spotDL` và chỉ hỗ trợ tải audio từ link track/album/playlist/artist. (Yêu cầu cấu hình credentials trong `.env`).
- `douyin` dùng module chuyên dụng `jiji262/douyin-downloader`, hỗ trợ tải no-watermark và batch profile. Truyền thêm mode thay vì option thông thường (`post`, `like`, `mix`, `music`, `favorites`). (Yêu cầu cấu hình 5 giá trị cookie trong `.env`).
- `mda dld update`: tự động kiểm tra và nâng cấp `yt-dlp` lên phiên bản mới nhất từ PyPI.
- Option yt-dlp: `best-vid`, `good-vid`, `audio`, `sub`, `thumb`, `img`; mặc định là `good-vid`.

Ví dụ:

```bash
mda dld update
mda dld ytb "https://youtube.com/watch?v=..." good-vid --threads 8
mda dld soundcloud "https://soundcloud.com/artist/track" audio --format mp3
mda dld spotify "https://open.spotify.com/playlist/..." audio --folder "D:\Music" --format mp3
```

### Tiện Ích

- `mda open`: mở project trong VS Code.
- `mda open -a`: mở project trong Antigravity IDE.
- `mda open -f`: mở thư mục project trong File Explorer.
- `mda git commit -m "<message>"`: chạy helper commit/push.
- `mda <type> <action> --des`: in mô tả chi tiết từ catalog `src/contents/app_features.yml`.

## Yêu Cầu

- Python 3.x.
- Cài dependency Python chính:

```bash
python -m pip install -r requirements.txt
```

- FFmpeg trong `PATH` cho các tính năng xử lý audio/video/media.
- `aria2c` trong `PATH` cho downloader.
- `spotDL` là dependency tùy chọn cho `mda dld spotify`; nên cài tách biệt bằng `pipx` để tránh xung đột dependency với môi trường Python chính:

```bash
python -m pip install --user pipx
python -m pipx ensurepath
python -m pipx install spotdl
```

Sau khi `ensurepath`, mở terminal mới để PATH có hiệu lực.

## Hướng Dẫn Thiết Lập (Khi Tải Về Máy Mới)

Để công cụ này hoạt động trên một máy tính mới, hãy làm theo các bước sau:

1. **Cài đặt thư viện Python:**
   Mở terminal tại thư mục gốc của dự án và chạy file `ins.cmd` hoặc gõ lệnh:
   ```bash
   python -m pip install -r requirements.txt
   ```

2. **Cấu hình đường dẫn dự án:**
   Mở file `src/configs/paths.py` và sửa biến `ROOT_FOLDER_PATH` thành đường dẫn tuyệt đối trỏ tới thư mục chứa dự án này trên máy của bạn. Ví dụ:
   ```python
   ROOT_FOLDER_PATH = "C:/Users/YourName/Downloads/media-studio"
   ```

3. **Thiết lập lệnh `mda` toàn cục (Thêm vào PATH):**
   - Copy đường dẫn thư mục gốc của dự án (nơi chứa file `mda.cmd`).
   - Mở cài đặt **Environment Variables** trên Windows -> Chọn **Path** -> Bấm **Edit** -> **New** -> Dán đường dẫn vừa copy vào.
   - Nhấn OK để lưu lại. Mở một terminal mới (hoặc CMD/PowerShell) để biến môi trường có hiệu lực.
   - Giờ bạn có thể gõ lệnh `mda` ở bất kỳ thư mục nào trên máy tính. *(File `mda.cmd` đã được tối ưu để tự tìm đúng mã nguồn).*

## Cấu Trúc Project Hiện Tại

```text
media-studio/
├── data/
│   ├── audio/
│   ├── credentials/
│   ├── image/
│   └── video/
│       ├── input/
│       └── output/
├── src/
│   ├── apps/
│   │   └── video_player/
│   ├── configs/
│   ├── contents/
│   ├── features/
│   │   ├── audio/
│   │   ├── downloader/
│   │   ├── image/
│   │   ├── media/
│   │   ├── system/
│   │   ├── useful/
│   │   └── video/
│   ├── utils/
│   └── main.py
├── mda.cmd
├── ins.cmd
├── requirements.txt
├── ARCHITECTURE.md
└── README.md
```

## Thư Mục Dữ Liệu

Cấu trúc dữ liệu đã được chuyển ra thư mục `data/` ở root project:

- Video input: `data/video/input/`
- Video output: `data/video/output/`
- Audio: `data/audio/`
- Image: `data/image/`
- Credentials/cookies: `data/credentials/`

Ví dụ cookie Douyin có thể đặt trong `data/credentials/` và truyền qua:

```bash
mda dld douyin "https://v.douyin.com/..." --cookies "data\credentials\cookies.txt"
```

## Cấu Trúc Source

- `src/main.py`: CLI dispatcher trung tâm.
- `src/apps/video_player/`: app GUI phát và so sánh video.
- `src/features/audio/`: tính năng audio.
- `src/features/video/`: tính năng video.
- `src/features/image/`: tính năng image.
- `src/features/media/`: cắt/chia file media.
- `src/features/downloader/`: downloader đa nền tảng.
- `src/features/system/`: helper hệ thống, hiện có `_media_studio_git.py` và `_print_feature_description.py`.
- `src/contents/`: help text và catalog mô tả tính năng.
- `src/configs/`: cấu hình JSON.
- `src/utils/`: helper dùng chung.

## Tra Cứu Nhanh

```bash
mda --help
mda dld --des
mda video frames --des
```
