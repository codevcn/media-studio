**Hướng Dẫn Tích Hợp jiji262/douyin-downloader vào Media Studio CLI (mda)**

**Phiên bản:** 2.0 (tháng 5/2026)  
**Tác giả:** Media Studio Development Team  
**Mục đích:** Hướng dẫn chi tiết, tuân thủ nghiêm ngặt kiến trúc hệ thống CLI dispatcher và module `src/features/downloader/` để nâng cấp tính năng tải Douyin hiện tại (dựa trên yt-dlp) bằng công cụ chuyên biệt `jiji262/douyin-downloader`.

### 1. Lý do tích hợp

Module `mda dld douyin` hiện tại sử dụng `yt-dlp` (qua `src/features/downloader/platform_downloaders.py`). Công cụ này hoạt động tốt với nhiều nền tảng nhưng đôi khi gặp hạn chế với anti-bot của Douyin (cookie thủ công, watermark không ổn định, batch profile chưa tối ưu).

`jiji262/douyin-downloader` là giải pháp **chuyên sâu cho Douyin** với các ưu điểm vượt trội:

- Tự động ưu tiên no-watermark và chất lượng cao nhất.
- Batch download toàn profile (post, like, mix, music, favorites collection) kèm deduplication SQLite.
- Browser fallback (Playwright) xử lý anti-bot hiệu quả.
- Hỗ trợ livestream recording, comment extraction, transcription.
- REST API server (FastAPI) và Docker sẵn dùng.
- Cập nhật thường xuyên (phiên bản mới nhất tháng 4/2026).

Tích hợp sẽ nâng cấp lệnh `mda dld douyin` (hoặc thêm action `douyin-advanced`) mà **không phá vỡ giao diện CLI hiện tại** và vẫn tận dụng cấu trúc dữ liệu `data/video/output/` cùng `data/credentials/`.

### 2. Yêu cầu trước khi tích hợp

- Project mda đã được clone và đang hoạt động (có `src/main.py`, `src/features/downloader/`, `data/credentials/`).
- Python 3.8+ và các dependency chính (`requirements.txt`).
- FFmpeg, aria2c đã cài đặt (theo README.md).
- Git đã được cấu hình (khuyến nghị dùng submodule).

### 3. Bước 1: Thêm douyin-downloader vào project

**Cách khuyến nghị (git submodule – dễ cập nhật và giữ code sạch):**

```bash
cd /path/to/media-studio
mkdir -p src/external
git submodule add https://github.com/jiji262/douyin-downloader.git src/external/douyin-downloader
git submodule update --init --recursive
```

**Hoặc copy thủ công:**

```bash
git clone https://github.com/jiji262/douyin-downloader.git src/external/douyin-downloader
```

**Cài dependencies:**

```bash
cd src/external/douyin-downloader
pip install -r requirements.txt

# Browser fallback (khuyến nghị)
pip install playwright
python -m playwright install chromium
```

**Tạo file config mẫu:**

```bash
cp config.example.yml config.yml
# Chỉnh sửa config.yml (đường dẫn database, notification, v.v.)
# Khuyến nghị đặt database tại: data/credentials/douyin-downloader.db
```

**Lưu ý quan trọng:**

- Thêm các dòng sau vào `.gitignore`:
  ```
  src/external/douyin-downloader/config.yml
  src/external/douyin-downloader/dy_downloader.db
  src/external/douyin-downloader/__pycache__/
  ```

### 4. Bước 2: Tạo wrapper trong module downloader

Tạo file mới: `src/features/downloader/douyin_downloader.py`

Nội dung chính (tuân thủ kiến trúc):

```python
#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

# Đường dẫn tuyệt đối
DOUYIN_DOWNLOADER_DIR = Path(__file__).parent.parent.parent / "external" / "douyin-downloader"
DEFAULT_OUTPUT = Path(__file__).parent.parent.parent.parent / "data" / "video" / "output"

def parse_args():
    parser = argparse.ArgumentParser(description="Tải media từ Douyin bằng jiji262/douyin-downloader")
    parser.add_argument("url", nargs="?", help="URL Douyin (video/profile/collection...)")
    parser.add_argument("--config", "-c", default="config.yml", help="Đường dẫn config.yml")
    parser.add_argument("--folder", "-p", default=str(DEFAULT_OUTPUT), help="Thư mục lưu (mặc định: data/video/output)")
    parser.add_argument("--mode", choices=["post", "like", "mix", "music", "favorites"], help="Chế độ batch")
    parser.add_argument("--threads", "-t", type=int, default=5, help="Số luồng tải")
    parser.add_argument("--cookies", help="Đường dẫn cookies.txt (tự động dùng data/credentials/)")
    parser.add_argument("--info", action="store_true", help="Hiển thị mô tả chi tiết")
    return parser.parse_args()

def main():
    args = parse_args()
    if args.info:
        print("Tích hợp douyin-downloader: hỗ trợ single/batch download Douyin chuyên sâu (no-watermark, deduplication, browser fallback).")
        sys.exit(0)

    if not args.url:
        print("Lỗi: Vui lòng cung cấp URL Douyin.")
        sys.exit(1)

    cmd = [
        "python", str(DOUYIN_DOWNLOADER_DIR / "run.py"),
        "-c", str(DOUYIN_DOWNLOADER_DIR / args.config),
        "-u", args.url,
        "-p", args.folder,
        "-t", str(args.threads)
    ]

    # Tự động hỗ trợ cookies từ data/credentials/
    if args.cookies:
        cmd.extend(["--cookies", args.cookies])
    elif (Path("data/credentials").glob("douyin-cookies*.txt")):
        cookie_file = next(Path("data/credentials").glob("douyin-cookies*.txt"))
        cmd.extend(["--cookies", str(cookie_file)])

    result = subprocess.run(cmd, cwd=DOUYIN_DOWNLOADER_DIR, check=False)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
```

### 5. Bước 3: Cập nhật dispatcher và downloader module

1. **Cập nhật `src/features/downloader/platform_downloaders.py`** (hoặc `run_downloader.py`):
   - Thêm logic để khi platform = "douyin" và có flag `--advanced` thì gọi wrapper mới.

2. **Cập nhật `src/main.py`**:
   - Thêm hằng số:
     ```python
     APP_DLD_DOUYIN_ADVANCED = "douyin-advanced"
     ```
   - Thêm handler:
     ```python
     def run_douyin_advanced(value: str | None = None):
         cmd_args = ["python", f"{FEATURES_FOLDER_PATH}/downloader/douyin_downloader.py"]
         if value:
             cmd_args.append(value)
         result = subprocess.run(cmd_args, check=False)
         sys.exit(result.returncode)
     ```
   - Thêm nhánh dispatch tương ứng.

3. **Tích hợp vào lệnh `mda dld douyin`** (khuyến nghị):
   - Thêm tùy chọn `--advanced` trong `platform_downloaders.py` để chuyển sang douyin-downloader khi cần.

### 6. Bước 4: Cập nhật tài liệu

- **src/contents/help.txt**: Thêm vào phần Downloader:

  ```
  douyin-advanced     Tải Douyin bằng công cụ chuyên biệt (no-watermark, batch profile, deduplication)
  ```

- **src/contents/app_features.yml**: Thêm entry chi tiết cho action mới theo cấu trúc YAML hiện có.

- **README.md**: Cập nhật phần Downloader để ghi nhận tính năng mới.

### 7. Bước 5: Kiểm tra và commit

```bash
mda dld douyin-advanced "https://www.douyin.com/video/..." --info
mda dld douyin-advanced "https://www.douyin.com/user/..." --folder "data/video/output"
```

Sau khi test thành công:

- Chạy `mda git commit -m "feat: tích hợp jiji262/douyin-downloader cho Douyin"`
- Push thay đổi.

### 8. Tùy chọn nâng cao (sau khi tích hợp cơ bản)

- Chạy REST API server của douyin-downloader trong background.
- Đồng bộ database deduplication với thư mục `data/video/output/`.
- Tích hợp tự động cookie fetcher từ `data/credentials/`.

### 9. Lưu ý bảo trì

- Cập nhật submodule: `git submodule update --remote src/external/douyin-downloader`
- Kiểm tra xung đột dependency giữa hai project.
- Luôn test trên môi trường staging trước.

Việc tích hợp hoàn tất sẽ mang lại trải nghiệm tải Douyin **chuyên nghiệp, ổn định và tối ưu hơn hẳn** so với yt-dlp thuần túy.

Nếu cần file code mẫu đầy đủ hơn (ví dụ: patch chính xác cho `platform_downloaders.py` hoặc `main.py`), hoặc hỗ trợ triển khai cụ thể, vui lòng cung cấp thêm chi tiết.
