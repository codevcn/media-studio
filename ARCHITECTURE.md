# Media Studio Architecture

Tài liệu này mô tả kiến trúc hiện tại của Media Studio CLI (`mda`) sau khi cấu trúc thư mục đã được gom lại theo nhóm `src/features/*` và dữ liệu runtime được chuyển ra thư mục `data/` ở root project.

## 1. Mục Tiêu

Media Studio là một bộ công cụ cá nhân để:

- Gom nhiều thao tác media vào một CLI ngắn: `mda`.
- Điều phối lệnh từ một dispatcher trung tâm.
- Tách mỗi nhóm nghiệp vụ thành script hoặc module độc lập.
- Dùng các tool đã ổn định như FFmpeg, yt-dlp, aria2c, spotDL và jiji262/douyin-downloader thay vì tự viết lại logic domain lớn.
- Giữ dữ liệu input/output, cookies và tài liệu nghiên cứu tách khỏi source code.

## 2. Luồng Tổng Thể

```text
User
  |
  v
mda.cmd
  |
  v
python src/main.py <type> <action> [value] [extra] [limit] [flags]
  |
  v
argparse + dispatcher
  |
  +-- app      -> src/apps/video_player/video_player.py
  +-- video    -> src/features/video/*.py
  +-- audio    -> src/features/audio/*.py
  +-- image    -> src/features/image/*.py
  +-- media    -> src/features/media/*.py
  +-- dld      -> src/features/downloader/run_downloader.py  (yt-dlp platforms)
  |              src/features/downloader/douyin_downloader.py (douyin riêng)
  +-- open     -> editor/File Explorer helper
  +-- git      -> src/features/system/_media_studio_git.py
  +-- --info   -> src/features/system/_print_feature_description.py (hỗ trợ alias --des)
```

Nguyên tắc chính: `src/main.py` chỉ parse, validate cấp CLI và gọi script con. Logic xử lý thực tế nằm trong từng nhóm feature.

## 3. Cấu Trúc Thư Mục

```text
media-studio/
├── .env                          # Credentials (Spotify, Douyin cookies)
├── data/
│   ├── audio/
│   ├── credentials/
│   ├── image/
│   └── video/
│       ├── input/
│       └── output/
├── doc/
│   ├── spotdl-spotify-downloader.md
│   └── tích hợp douyin downloader tool.md
├── src/
│   ├── apps/
│   │   └── video_player/
│   ├── configs/
│   ├── contents/
│   ├── external/
│   │   └── douyin-downloader/    # Git submodule (jiji262/douyin-downloader)
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
├── README.md
└── ARCHITECTURE.md
```

## 4. Vai Trò Từng Khu Vực

| Khu vực | Vai trò |
| --- | --- |
| `.env` | Credentials nhạy cảm: Spotify API keys, Douyin cookies. Không commit lên remote. |
| `mda.cmd` | Wrapper Windows gọi `python src/main.py %*`. |
| `ins.cmd` | Cài dependency Python từ `requirements.txt`. |
| `data/` | Dữ liệu runtime: media input/output, ảnh, audio, cookie/credential. |
| `doc/` | Ghi chú nghiên cứu và decision log cho các tích hợp đặc biệt. |
| `src/main.py` | CLI dispatcher trung tâm. |
| `src/apps/` | Ứng dụng GUI. Hiện có video player kép. |
| `src/external/` | Công cụ bên thứ ba dạng git submodule (hiện có `douyin-downloader`). |
| `src/features/audio/` | Script xử lý audio. |
| `src/features/video/` | Script xử lý video. |
| `src/features/image/` | Script xử lý image. |
| `src/features/media/` | Script cắt/chia file media dùng chung cho audio/video. |
| `src/features/downloader/` | Downloader đa nền tảng (yt-dlp, spotDL, douyin wrapper). |
| `src/features/system/` | Helper hệ thống, ví dụ git commit/push. |
| `src/features/useful/` | Helper tiện ích, ví dụ in mô tả tính năng từ YAML. |
| `src/contents/` | Nội dung tĩnh cho help và catalog feature. |
| `src/configs/` | Config đường dẫn dự án. |
| `src/utils/` | Helper dùng chung. |

## 5. CLI Grammar

Cú pháp tổng quát:

```text
mda <type> <action> [value] [extra] [limit] [flags]
```

Các type hiện có:

| Type | Ý nghĩa |
| --- | --- |
| `app` | App GUI. |
| `video` | Xử lý video. |
| `audio` | Xử lý âm thanh. |
| `image` | Xử lý hình ảnh. |
| `media` | Xử lý media chung. |
| `dld` | Downloader đa nền tảng. |
| `open` | Mở project. |
| `git` | Helper Git. |

Flag đáng chú ý:

- `--info`: in mô tả chi tiết từ `src/contents/app_features.yml` (vẫn hỗ trợ alias `--des`).
- `--filename`, `--folder`, `--format`, `--threads`: dùng cho downloader.
- `--cookies`, `--cookies-from-browser`: dùng cho downloader khi platform cần cookie.
- `-m`, `--message`: dùng cho `mda git commit`.
- `-a`, `--anti`: mở bằng Antigravity IDE thay vì VS Code.
- `-f`, `--file_explorer`: mở project bằng File Explorer.

## 6. Dispatcher

`src/main.py` giữ các trách nhiệm:

- Load `.env`.
- Định nghĩa constant type/action.
- Parse CLI bằng `argparse`.
- Validate tham số cấp dispatcher.
- Build command list để gọi script con bằng `subprocess.run`.
- Điều hướng `--info` (và `--des`) sang `src/features/system/_print_feature_description.py`.
- Điều hướng `git commit` sang `src/features/system/_media_studio_git.py`.

Các handler không nên chứa logic xử lý media nặng. Ví dụ `run_media_slice(...)` chỉ kiểm tra tham số bắt buộc, build command và gọi `src/features/media/slice_media.py`.

## 7. Downloader Architecture

Downloader có 4 file chính:

```text
src/features/downloader/
├── base_downloader.py
├── platform_downloaders.py
├── run_downloader.py
└── douyin_downloader.py
```

### `run_downloader.py`

Vai trò:

- Parse riêng các flag downloader.
- Map platform string sang class downloader.
- Khởi tạo downloader và gọi `.download()`.

Platform hiện có (qua yt-dlp / spotDL):

```text
ytb, ytb-music, fb, insta, tiktok,
bilibili, bili, bilili, soundcloud, scloud, spot
```

Lưu ý: `douyin` được điều phối riêng từ `main.py` sang `douyin_downloader.py`, không đi qua `run_downloader.py`.

### `base_downloader.py`

Vai trò:

- Build command `yt-dlp`.
- Map option `best-vid`, `good-vid`, `audio`, `sub`.
- Áp dụng `--format`, `--folder`, `--filename`.
- Áp dụng cookies.
- Áp dụng aria2 external downloader.
- In lỗi gợi ý thân thiện.

### `platform_downloaders.py`

Vai trò:

- Định nghĩa class theo platform.
- Các platform thông thường kế thừa `BaseDownloader`.
- Platform có behavior riêng override method tương ứng.

Các điểm đặc biệt:

- `FacebookDownloader` override good video format để fallback ổn hơn.
- `TiktokDownloader` override `download()` để thử tải bản **no-watermark** (format `download_addr-0`) trước. Nếu thất bại, in cảnh báo và fallback sang bản có watermark qua `BaseDownloader`.
- `SoundCloudDownloader` dùng `yt-dlp`, nhưng `good-vid`/`best-vid` được fallback sang audio vì SoundCloud là audio-first.
- `SpotifyDownloader` không dùng `yt-dlp` trực tiếp, mà gọi `spotdl download`. Yêu cầu `SPOTIFY_CLIENT_ID` và `SPOTIFY_CLIENT_SECRET` trong `.env`.

### `douyin_downloader.py`

Vai trò:

- Wrapper chuyên cho Douyin, gọi submodule `jiji262/douyin-downloader` (`src/external/douyin-downloader/run.py`).
- Đọc 5 biến cookie Douyin từ `.env`, kiểm tra đủ hay chưa. Nếu thiếu: in hướng dẫn lấy cookie từ trình duyệt và dừng.
- Nếu đủ cookie: inject vào `config.yml` của submodule rồi chạy.
- Hỗ trợ batch download qua `--mode` (post, like, mix, music, favorites).
- Thư mục lưu mặc định là thư mục hiện tại (CWD).

## 8. Spotify Và spotDL

Spotify được tách thành downloader riêng vì pipeline `yt-dlp` hiện tại không phù hợp để tải Spotify như các platform khác.

Quy ước hiện tại:

- `mda dld spotify ...` chỉ hỗ trợ audio.
- `sub` không hợp lệ với Spotify.
- `spotDL` là dependency tùy chọn, không nằm trong `requirements.txt`.
- `spotDL` nên được cài bằng `pipx` để tránh xung đột dependency trong Python chính.

Ví dụ:

```bash
python -m pip install --user pipx
python -m pipx ensurepath
python -m pipx install spotdl
```

Tài liệu chi tiết nằm ở:

```text
doc/spotdl-spotify-downloader.md
```

## 8b. Douyin Và jiji262/douyin-downloader

Douyin được tách thành luồng riêng vì `yt-dlp` không ổn định cho Douyin (anti-bot mạnh). Thay vào đó dùng công cụ chuyên dụng `jiji262/douyin-downloader` được tích hợp dạng git submodule.

Quy ước hiện tại:

- `mda dld douyin ...` đi riêng qua `src/features/downloader/douyin_downloader.py`, không qua `run_downloader.py`.
- Bắt buộc phải có 5 biến cookie Douyin trong `.env` (`DOUYIN_MS_TOKEN`, `DOUYIN_TTWID`, `DOUYIN_ODIN_TT`, `DOUYIN_PASSPORT_CSRF_TOKEN`, `DOUYIN_SID_GUARD`).
- Hỗ trợ batch download (tải toàn bộ profile/collection) qua `--mode post|like|mix|music|favorites`.
- Submodule yêu cầu cài dependency riêng (bao gồm `playwright` và trình duyệt Chromium).
- Sau khi clone project lần đầu cần chạy `git submodule update --init --recursive`.

Tài liệu tích hợp chi tiết nằm ở:

```text
doc/tích hợp douyin downloader tool.md
```

## 9. Data Architecture

Dữ liệu runtime nằm ở root `data/`:

```text
data/
├── audio/
├── credentials/
├── image/
└── video/
    ├── input/
    └── output/
```

Ý nghĩa:

- `data/video/input/`: video nguồn.
- `data/video/output/`: video kết quả.
- `data/audio/`: audio input/output hoặc file tách âm.
- `data/image/`: ảnh input/output.
- `data/credentials/`: cookies hoặc file credential cục bộ.

Không commit credential thật hoặc file nhạy cảm nếu repo được đẩy lên remote.

## 10. GUI Video Player

App nằm tại:

```text
src/apps/video_player/video_player.py
```

Chức năng:

- Phát 2 video song song.
- Quét danh sách video input/output.
- Hiển thị sidebar cặp video.
- Hỗ trợ shortcut playback, seek, volume và chọn nguồn audio.

Dependency chính:

- `PySide6`
- `opencv-python`

Ghi chú migration: quy ước dữ liệu mới là `data/video/input` và `data/video/output`. Khi chỉnh video player hoặc config liên quan, nên đồng bộ về quy ước này để tránh quay lại path cũ `src/data/media/...`.

## 11. Feature Catalog Và Help

Hai file nội dung tĩnh:

```text
src/contents/help.txt
src/contents/app_features.yml
```

Vai trò:

- `help.txt`: nội dung help ngắn khi chạy `mda --help`.
- `app_features.yml`: catalog có cấu trúc cho `mda <type> <action> --info`.

Khi thêm hoặc đổi command, cập nhật đồng thời:

1. Constant và dispatch trong `src/main.py`.
2. Handler hoặc script feature.
3. Help ngắn trong `src/contents/help.txt`.
4. Mô tả chi tiết trong `src/contents/app_features.yml`.
5. README nếu ảnh hưởng cách dùng.
6. Tài liệu trong `doc/` nếu là tích hợp phức tạp.

## 12. External Tools

| Tool | Dùng cho |
| --- | --- |
| FFmpeg | Cắt, chia, encode/copy stream, tách audio, xóa logo, trích frame. |
| ffprobe | Đọc metadata media cho chia theo dung lượng. |
| yt-dlp | Downloader chính cho nhiều platform (YouTube, FB, TikTok, Bilibili...). |
| aria2c | Tăng tốc download qua external downloader của yt-dlp. |
| spotDL | Downloader audio cho Spotify (CLI optional, cài qua pipx). |
| jiji262/douyin-downloader | Downloader chuyên Douyin (git submodule trong `src/external/`). |
| Playwright + Chromium | Hỗ trợ anti-bot cho douyin-downloader. |
| Git | Helper `mda git commit`. |

Python packages chính trong `requirements.txt`:

```text
python-dotenv
opencv-python
Pillow
PySide6
PyYAML
yt-dlp
```

`spotDL` và dependency của `douyin-downloader` không nằm trong `requirements.txt` chính.

## 13. Mở Rộng Feature

Khi thêm một feature mới:

1. Chọn nhóm thư mục trong `src/features/<group>/`.
2. Tạo script có thể chạy độc lập.
3. Thêm constant action trong `src/main.py`.
4. Thêm handler build command trong `src/main.py`.
5. Thêm nhánh dispatch.
6. Cập nhật `help.txt` và `app_features.yml`.
7. Cập nhật README nếu người dùng cần biết.
8. Chạy kiểm tra.

Mẫu handler:

```python
def run_new_feature(input_path: str, option: str | None = None):
    if not input_path:
        raise Exception("MISSING-ACTION - Cần truyền input_path")

    script_path = get_script_path("features/<group>/new_feature.py")
    cmd = [sys.executable, script_path, input_path]
    if option:
        cmd.append(option)
    subprocess.run(cmd)
    sys.exit(0)
```

## 14. Kiểm Tra

Kiểm tra nhanh sau khi chỉnh code:

```bash
python -m compileall -q src
python src\main.py --help
python src\main.py dld spotify --info
python src\features\downloader\run_downloader.py unknown https://example.com
```

Kiểm tra dependency:

```bash
python -m pip check
```

Kiểm tra markdown/diff cơ bản:

```bash
git diff --check
```

## 15. Migration Notes

Các thay đổi cấu trúc quan trọng gần đây:

- `src/system-codes/` đã được thay bằng `src/features/system/`.
- `src/useful-codes/` đã được thay bằng `src/features/useful/`.
- Dữ liệu runtime chuyển từ kiểu cũ `src/data/media/...` sang `data/...` ở root project.
- Downloader thêm `soundcloud` (alias `scloud`) qua `yt-dlp`.
- Downloader thêm `spotify` qua `spotDL`.
- `spotDL` từng được thử đưa vào `requirements.txt` nhưng gây xung đột dependency; hiện được coi là CLI optional cài qua `pipx`.
- `DouyinDownloader` (phiên bản yt-dlp cũ) đã bị xóa hoàn toàn. Thay thế bằng `douyin_downloader.py` wrapper gọi submodule `jiji262/douyin-downloader`.
- Douyin được tách khỏi luồng `run_downloader.py`, có dispatcher riêng trong `main.py` (`run_douyin_advanced`).
- Credentials (Spotify API, Douyin cookies) quản lý tập trung trong file `.env` ở root project.
- `TiktokDownloader` nâng cấp: ưu tiên tải no-watermark (format `download_addr-0`), tự fallback sang bản có watermark nếu thất bại.
- Thêm thư mục `src/external/` chứa git submodule. Sau khi clone cần chạy `git submodule update --init --recursive`.

Khi gặp path cũ trong source hoặc config, ưu tiên cập nhật về cấu trúc hiện tại thay vì tạo lại thư mục legacy.
