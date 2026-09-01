# Tính Năng `dld` — Media Studio Downloader

> Tài liệu mô tả chi tiết tính năng tải xuống đa nền tảng (`dld`) trong Media Studio CLI (`mda`).

---

## 1. Tổng Quan

`dld` (viết tắt của **download**) là nhóm lệnh cho phép tải video, audio, phụ đề, thumbnail và ảnh từ các nền tảng mạng xã hội phổ biến trực tiếp qua CLI.

Cú pháp tổng quát:

```bash
mda dld <platform> <url> [--option <opt>] [--filename <name>] [--folder <path>] [--format <ext>] [--threads <n>] [--slice <time>] [--mode <mode>]
```

---

## 2. Nền Tảng Được Hỗ Trợ

| Alias (platform) | Nền Tảng | Engine |
|---|---|---|
| `ytb` | YouTube | yt-dlp + aria2c |
| `ytb-music` | YouTube Music | yt-dlp + aria2c |
| `fb` | Facebook | yt-dlp + aria2c |
| `insta` | Instagram | yt-dlp + aria2c |
| `tiktok` | TikTok | yt-dlp + aria2c (thử no-watermark trước) |
| `twitter` / `x` | Twitter (X) | yt-dlp + aria2c (qua Syndication API) |
| `bilibili` / `bili` / `bilili` | Bilibili | yt-dlp + aria2c |
| `soundcloud` / `scloud` | SoundCloud | yt-dlp + aria2c (chỉ audio) |
| `spot` | Spotify | spotDL CLI |
| `douyin` | Douyin | jiji262/douyin-downloader (submodule) |

Xem nhanh danh sách hoặc cập nhật:

```bash
mda dld list
mda dld update
```

---

## 3. Các Tùy Chọn (Flags)

### 3.1 `--option <opt>` — Chất lượng / Loại nội dung tải

| Giá trị | Ý nghĩa | Định dạng yt-dlp |
|---|---|---|
| `good-vid` *(mặc định)* | Video 720p, cân bằng chất lượng/dung lượng | `bv*[height<=720]+ba/b[height<=720] / wv*+ba/w` |
| `best-vid` | Video chất lượng cao nhất | `bv*+ba/b` |
| `audio` | Chỉ tải audio (chuyển đổi qua `--format`, mặc định `mp3`) | `-x --audio-format <fmt>` |
| `sub` | Chỉ tải phụ đề (không tải video; không dùng aria2c) | `--write-subs --write-auto-subs --skip-download` |
| `thumb` | Chỉ tải ảnh bìa thumbnail (không tải video; không dùng aria2c) | `--write-thumbnail --skip-download` |
| `img` | Tải toàn bộ ảnh trong link | `--write-all-thumbnails -f bestimage/...` |

> **Lưu ý auto-detect**: Nếu `--format` là định dạng audio (`mp3`, `m4a`, `wav`, `flac`, `opus`, `vorbis`, `aac`, `alac`) nhưng `--option` lại là video (`best-vid`, `good-vid`), hệ thống **tự động chuyển** `--option` sang `audio` và thông báo.

---

### 3.2 `--format <ext>` — Định Dạng Đầu Ra

| Loại nội dung | Định dạng hợp lệ | Mặc định |
|---|---|---|
| Video (`good-vid`, `best-vid`) | `mp4`, `mkv`, `webm`, `ogg`, `flv` | Gốc của yt-dlp |
| Audio (`--option audio`) | `mp3`, `m4a`, `wav`, `flac`, `opus`, `vorbis`, `aac`, `alac` | `mp3` |
| Phụ đề (`--option sub`) | `srt`, `vtt`, `ass`, `lrc` | `srt` |
| Thumbnail (`--option thumb`) | `jpg`, `png`, `webp` | Gốc của nền tảng |
| Spotify | `mp3`, `m4a`, `wav`, `flac`, `opus`, `vorbis`, `aac`, `alac` | `mp3` |

---

### 3.3 `--filename <name>` — Tên File Đầu Ra

Chỉ định tên file không bao gồm phần mở rộng. Hệ thống tự thêm `.%(ext)s` (yt-dlp) hoặc `.{output-ext}` (Spotify).

```bash
# Ví dụ: tải YouTube, đặt tên file là "my_video"
mda dld ytb "https://youtube.com/watch?v=..." --filename "my_video"
```

---

### 3.4 `--folder <path>` — Thư Mục Lưu

Chỉ định thư mục đích để lưu file. Mặc định: thư mục hiện tại (CWD).

```bash
mda dld ytb "https://youtube.com/..." --folder "D:\Downloads\YouTube"
```

---

### 3.5 `--threads <n>` — Số Luồng Tải (aria2c)

Số kết nối song song của aria2c khi tải (số nguyên `>= 1`, mặc định `4`).

- Không áp dụng khi `--option sub`, `thumb`, hoặc `img`.
- Douyin mặc định dùng `5` luồng.

```bash
mda dld ytb "https://youtube.com/..." --threads 8
```

---

### 3.6 `--slice <time>` — Cắt Đoạn Thời Gian Khi Tải (Chỉ YouTube / YT Music)

Cú pháp: `HH:MM:SS-HH:MM:SS` (hoặc theo giây).

Truyền qua yt-dlp flag: `--download-sections *<time>`.

```bash
# Tải đoạn từ 00:10 đến 01:22
mda dld ytb "https://youtube.com/watch?v=..." --slice "00:10-01:22"
```

---

### 3.7 `--mode <mode>` — Chế Độ Batch (Chỉ Douyin)

| Giá trị | Ý nghĩa |
|---|---|
| `post` | Toàn bộ video đã đăng của profile |
| `like` | Toàn bộ video đã thích |
| `mix` | Theo mix/playlist |
| `music` | Theo nhạc |
| `favorites` | Video đã lưu (favorites) |

```bash
mda dld douyin "https://www.douyin.com/user/..." --mode post --folder "D:\Douyin"
```

---

## 4. Kiến Trúc Module Downloader

```
src/features/downloader/
├── base_downloader.py        # Lớp cơ sở, build lệnh yt-dlp + aria2c
├── platform_downloaders.py   # Các class theo nền tảng (kế thừa BaseDownloader)
├── run_downloader.py         # Entry point: parse args, map platform → class
└── douyin_downloader.py      # Wrapper riêng cho Douyin (gọi submodule)
```

### 4.1 `BaseDownloader`

Lớp cơ sở dùng cho tất cả nền tảng trừ Spotify và Douyin. Chịu trách nhiệm:

- **Build lệnh yt-dlp** hoàn chỉnh dựa trên `option`, `filename`, `folder`, `format`, `threads`.
- **Auto-detect audio format** (nếu `--format` là audio nhưng `--option` là video thì chuyển sang `audio`).
- **Áp dụng aria2c** với multi-connection (`-x <threads> -s <threads> -k 1M`) cho tất cả option trừ `sub`, `thumb`, `img`.
- **Xử lý lỗi** thân thiện: gợi ý khắc phục khi yt-dlp thất bại, thiếu aria2c, hoặc video bị khóa.

**Phương thức chính:**

| Phương thức | Mô tả |
|---|---|
| `download()` | Thực thi tải xuống, bắt và xử lý lỗi |
| `build_command()` | Build danh sách args yt-dlp hoàn chỉnh |
| `set_best_video_options()` | Áp dụng format video chất lượng cao nhất |
| `set_good_video_options()` | Áp dụng format video 720p |
| `set_audio_options()` | Áp dụng chế độ tải audio (`-x --audio-format`) |
| `set_sub_options()` | Áp dụng chế độ chỉ tải phụ đề |
| `set_thumb_options()` | Áp dụng chế độ chỉ tải thumbnail |
| `set_img_options()` | Áp dụng chế độ tải toàn bộ ảnh |
| `apply_aria2_options()` | Thêm `--external-downloader aria2c` vào lệnh |

---

### 4.2 `platform_downloaders.py` — Class Theo Nền Tảng

#### `YoutubeDownloader` & `YoutubeMusicDownloader`
Kế thừa `BaseDownloader`. Thêm `--download-sections *<slice>` khi có tham số `--slice`.

#### `FacebookDownloader`
Ghi đè `set_good_video_options()` với fallback selector ổn hơn cho FB:
```
bv*[height<=720]+ba/bestvideo[height<=720]+bestaudio/best
```

#### `TiktokDownloader`
Cơ chế **no-watermark ưu tiên**:
1. Thử tải format `download_addr-0` (bản không watermark của TikTok).
2. Nếu thất bại → in cảnh báo → **fallback tự động** sang luồng yt-dlp thông thường (có thể kèm watermark).
3. Không áp dụng cơ chế này cho `audio`/`sub`.

#### `BilibiliDownloader`
Kế thừa nguyên `BaseDownloader`. Hỗ trợ 3 alias: `bilibili`, `bili`, `bilili`.

#### `SoundCloudDownloader`
- Kế thừa `BaseDownloader`.
- Ghi đè cả `set_good_video_options()` và `set_best_video_options()` để chuyển về `set_audio_options()` — vì SoundCloud là audio-first, không có video.

#### `TwitterDownloader`
- Ghi đè `build_command()`: thêm `--extractor-args twitter:api=syndication` để tránh lỗi "Bad guest token".
- Ghi đè `download()`: khi `--option img`, dùng **vxtwitter API** (`api.vxtwitter.com`) thay vì yt-dlp để tải ảnh.
  - Trích xuất tweet ID từ URL.
  - Gọi API lấy danh sách `mediaURLs`.
  - Tải từng ảnh bằng `urllib.request.urlretrieve`.
  - Hỗ trợ đặt tên theo `--filename`, `--folder`.
  - Tự động thêm hậu tố `_0`, `_1`... nếu bài có nhiều ảnh.

#### `SpotifyDownloader`
Không kế thừa `BaseDownloader`. Dùng **spotDL CLI** thay vì yt-dlp.

- Chỉ hỗ trợ audio (sub không hợp lệ).
- Đọc `SPOTIFY_CLIENT_ID` và `SPOTIFY_CLIENT_SECRET` từ `.env`. Nếu thiếu → dừng và in hướng dẫn lấy credential.
- Build lệnh: `spotdl download <url> --format <fmt> --threads <n> --client-id ... --client-secret ...`
- Output template: `{artists} - {title}.{output-ext}` hoặc tùy chỉnh qua `--filename`.
- Là dependency tùy chọn, **không nằm trong `requirements.txt`** (cài qua `pipx install spotdl`).

---

### 4.3 `douyin_downloader.py` — Wrapper Chuyên Douyin

Douyin có cơ chế anti-bot mạnh nên **không dùng yt-dlp**. Thay vào đó tích hợp submodule chuyên dụng `jiji262/douyin-downloader` tại:

```
src/external/douyin-downloader/
```

**Luồng hoạt động:**
1. Parse tham số: `url`, `--folder`, `--mode`, `--threads`.
2. Xây dựng lệnh gọi `src/external/douyin-downloader/run.py` với `-c config.yml -u <url> -p <folder> -t <threads> [--mode <mode>]`.
3. Chạy subprocess với `cwd=DOUYIN_DOWNLOADER_DIR`.

**Cookies Douyin (`.env`):** Submodule yêu cầu 5 biến cookie từ trình duyệt:

| Biến | Mô tả |
|---|---|
| `DOUYIN_MS_TOKEN` | ms_token |
| `DOUYIN_TTWID` | ttwid |
| `DOUYIN_ODIN_TT` | odin_tt |
| `DOUYIN_PASSPORT_CSRF_TOKEN` | passport_csrf_token |
| `DOUYIN_SID_GUARD` | sid_guard |

Lấy bằng cách: `F12` → `Application` → `Storage` → `Cookies` → `douyin.com`.

**Dependency riêng cho Douyin:**
- `playwright` (Python package)
- Trình duyệt Chromium (cài qua `playwright install`)
- Sau khi clone: `git submodule update --init --recursive`

---

## 5. Luồng Dispatch Tổng Thể

```
mda dld <platform> <url> [flags]
         │
         ▼
src/main.py (dispatcher)
         │
         ├── platform == "douyin"
         │       └── run_douyin_advanced()
         │               └── subprocess: douyin_downloader.py → external/douyin-downloader/run.py
         │
         ├── platform == "list"
         │       └── In danh sách nền tảng → exit
         │
         └── platform ∈ [ytb, ytb-music, fb, insta, tiktok, twitter, x,
                          bilibili, bili, bilili, soundcloud, scloud, spot]
                 └── run_downloader()
                         └── subprocess: run_downloader.py
                                 └── Map platform → DownloaderClass
                                         └── downloader.download()
                                                 └── yt-dlp + aria2c  (hoặc spotdl cho Spotify)
```

---

## 6. Ví Dụ Sử Dụng

```bash
# Tải YouTube 720p (mặc định)
mda dld ytb "https://youtube.com/watch?v=dQw4w9WgXcQ"

# Tải YouTube chất lượng cao nhất, 8 luồng
mda dld ytb "https://youtube.com/watch?v=..." best-vid --threads 8

# Tải YouTube, cắt từ 00:10 đến 01:22
mda dld ytb "https://youtube.com/watch?v=..." --slice "00:10-01:22"

# Tải audio từ YouTube, lưu thành mp3
mda dld ytb "https://youtube.com/watch?v=..." --option audio --format mp3

# Tải phụ đề tiếng Việt từ YouTube
mda dld ytb "https://youtube.com/watch?v=..." --option sub --format srt

# Tải thumbnail YouTube
mda dld ytb "https://youtube.com/watch?v=..." --option thumb --format jpg

# Tải TikTok (tự động thử no-watermark)
mda dld tiktok "https://vt.tiktok.com/..."

# Tải video Bilibili
mda dld bili "https://bilibili.com/video/..." --folder "D:\Bilibili" --threads 6

# Tải audio Bilibili thành mp3, đặt tên tùy chỉnh
mda dld bili "https://bilibili.com/video/..." --option audio --filename "my_audio" --folder "C:\Downloads" --format mp3

# Tải SoundCloud (tự động chuyển về audio)
mda dld scloud "https://soundcloud.com/artist/track" --option audio --format mp3

# Tải Spotify playlist (cần credentials trong .env)
mda dld spot "https://open.spotify.com/playlist/..." --folder "D:\Music" --format flac

# Tải Douyin single video
mda dld douyin "https://v.douyin.com/..."

# Tải toàn bộ video đăng của user Douyin
mda dld douyin "https://www.douyin.com/user/..." --mode post --folder "D:\Douyin" --threads 5

# Tải ảnh từ Twitter/X
mda dld twitter "https://twitter.com/user/status/..." --option img --folder "D:\Twitter"

# Xem mô tả chi tiết tính năng dld
mda dld --info
```

---

## 7. Yêu Cầu Phụ Thuộc

### 7.1 Phụ Thuộc Chung (hầu hết platform)

| Tool | Cài đặt |
|---|---|
| `yt-dlp` | `pip install yt-dlp` |
| `aria2c` | Tải từ [aria2.github.io](https://aria2.github.io/), thêm vào PATH |

### 7.2 Spotify

| Yêu cầu | Ghi chú |
|---|---|
| `spotdl` | `pipx install spotdl` *(không dùng pip thường để tránh conflict)* |
| Spotify API credentials | Tạo app tại [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard), điền `SPOTIFY_CLIENT_ID` và `SPOTIFY_CLIENT_SECRET` vào `.env` |

### 7.3 Douyin

| Yêu cầu | Ghi chú |
|---|---|
| Git submodule | `git submodule update --init --recursive` |
| `playwright` | `pip install playwright && playwright install` |
| Cookies Douyin | Điền 5 biến `DOUYIN_*` vào `.env` |

---

## 8. Xử Lý Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Gợi ý |
|---|---|---|
| `yt-dlp` hoặc `aria2c` không tìm thấy | Chưa cài hoặc chưa thêm vào PATH | Cài và thêm vào PATH hệ thống |
| yt-dlp thất bại (mã lỗi khác 0) | Video private, bị xóa, giới hạn tuổi, cookie hết hạn | Kiểm tra URL, thêm cookie, cập nhật `yt-dlp` |
| Spotify rate limit (`86400s`) | Dùng shared client ID mặc định của spotDL | Tạo app riêng tại Spotify Developer Dashboard |
| Douyin báo lỗi xác thực | Cookie hết hạn hoặc thiếu | Lấy lại cookie mới từ trình duyệt |
| TikTok tải có watermark | Format `download_addr-0` bị chặn | Bình thường — đây là fallback tự động |
| Twitter `Bad guest token` | API Twitter thay đổi | Đã được xử lý tự động qua `api=syndication` |
| Không tìm thấy ảnh Twitter | Bài không có ảnh / URL sai | Kiểm tra URL tweet chứa ảnh |

---

## 9. Cấu Hình `.env`

File `.env` ở thư mục gốc project quản lý tập trung credential nhạy cảm:

```ini
# Spotify Developer Credentials
SPOTIFY_CLIENT_ID=""
SPOTIFY_CLIENT_SECRET=""

# Douyin Browser Cookies
DOUYIN_MS_TOKEN=""
DOUYIN_TTWID=""
DOUYIN_ODIN_TT=""
DOUYIN_PASSPORT_CSRF_TOKEN=""
DOUYIN_SID_GUARD=""
```

> ⚠️ **Không commit file `.env` lên remote repository.**

---

## 10. Xem Mô Tả Chi Tiết Inline

```bash
# Xem mô tả tính năng dld ngay trong terminal
mda dld --info

# Hoặc xem toàn bộ tính năng
mda --help
```
