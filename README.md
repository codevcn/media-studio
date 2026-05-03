# Media Studio CLI (mda)

Media Studio là bộ công cụ CLI và GUI cá nhân để xử lý video, âm thanh, hình ảnh, media file và tải nội dung đa nền tảng.

## Tính Năng

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
- Các platform dùng `yt-dlp` + `aria2c`: `ytb`, `ytb-music`, `fb`, `insta`, `tiktok`, `douyin`, `bilibili`, `bili`, `bilili`, `soundcloud`.
- `spotify` dùng `spotDL` và chỉ hỗ trợ tải audio từ link track/album/playlist/artist.
- Option: `best-vid`, `good-vid`, `audio`, `sub`; mặc định là `good-vid`.
- Douyin tự thử cookies từ `chrome`, `edge`, `firefox` nếu không truyền cookie thủ công.

Ví dụ:

```bash
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
- `src/features/system/`: helper hệ thống, hiện có `media_studio_git.py`.
- `src/features/useful/`: helper tiện ích, hiện có `print_feature_description.py`.
- `src/contents/`: help text và catalog mô tả tính năng.
- `src/configs/`: cấu hình JSON.
- `src/utils/`: helper dùng chung.

## Tra Cứu Nhanh

```bash
mda --help
mda dld --des
mda video frames --des
```
