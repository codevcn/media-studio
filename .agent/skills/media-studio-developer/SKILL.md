---
name: media-studio-developer
description: >-
  Hướng dẫn toàn diện và quy chuẩn chuẩn hóa dành cho AI Agent khi THÊM, SỬA, hoặc XÓA
  các tính năng (types/actions) trong hệ thống Media Studio CLI (mda).
---

# Media Studio CLI Developer Skill (Master Standard)

Tài liệu này là **Quy chuẩn tác nghiệp chuẩn (SOP)** dành cho AI Agent khi thao tác trên codebase **Media Studio CLI (`mda`)**.

---

## 1. Kiến Trúc & Các Nguyên Tắc Bất Di Bất Dịch

```text
User: mda <type> <action> [value] [extra] [limit] [flags] [--des]
  │
  ├── mda.cmd / mda.ps1 (Launchers) ──► src/main.py (Central Dispatcher)
  │                                           │
  │     ┌─────────────────────────────────────┴─────────────────────────────────────┐
  │     ▼                                                                           ▼
  │  [Không đối số: len == 1]                                                 [Có đối số]
  │  src/utils/interactive_cli.py                                       argparse & handler functions
  │  (Chế độ REPL + Tab Autocomplete)                                               │
  │                                                                                 ▼
  └───────────────────────────────────────────────────────────────────► src/features/<module>/<script>.py
                                                                        (Thực thi nghiệp vụ FFmpeg / yt-dlp / Pillow / OCR / GUI)
```

### 4 Nguyên Tắc Cốt Lõi:
1. **Kiến trúc Dispatcher trung tâm (`src/main.py`):**
   - `src/main.py` là cổng điều phối duy nhất tiếp nhận tham số dòng lệnh từ người dùng.
   - Khi chạy `mda` không tham số: Kích hoạt REPL Interactive Session trong `src/utils/interactive_cli.py`.
   - Cờ toàn cục `--des`: Tự động gọi `src/features/system/_print_feature_description.py` để in catalog định dạng màu từ `src/contents/app_features.yml`.
2. **Không hardcode đường dẫn:** Mọi đường dẫn tuyệt đối hoặc tương đối đều phải xây dựng dựa trên `ROOT_FOLDER_PATH` trong [`src/configs/paths.py`](file:///d:/D-Documents/TOOLs/media-studio/src/configs/paths.py) hoặc helper `get_script_path()`.
3. **Mã hóa UTF-8 Console:** Luôn đặt hàm `ensure_utf8_stdout()` với `sys.stdout.reconfigure(encoding="utf-8")` ở đầu tất cả các script để đảm bảo hiển thị tiếng Việt chuẩn xác trên Windows terminal.
4. **Làm sạch URL (`clean_url`):** Khi làm việc với các tính năng downloader hoặc media URL, luôn gọi `clean_url(url, platform)` từ `src/utils/helpers.py` để loại bỏ tracking tags, bóc tách URL từ văn bản và loại bỏ tham số radio/mix YouTube gây lỗi.

---

## 2. SOP 1: Quy Trình THÊM Tính Năng Mới (Add Feature)

Khi nhận yêu cầu thêm lệnh mới (ví dụ: `mda <type> <action>`):

### Bước 1: Tạo Feature Script (`src/features/<module>/<tên_tính_năng>.py`)
- Cấu hình import `sys.path` trỏ về `src/` để import configs/utils:
  ```python
  import os
  import sys
  from pathlib import Path

  src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  if src_dir not in sys.path:
      sys.path.insert(0, src_dir)

  from configs.paths import ROOT_FOLDER_PATH
  ```
- Định nghĩa hàm `ensure_utf8_stdout()`.
- Xử lý logic nghiệp vụ (gọi FFmpeg qua subprocess, xử lý file bằng Pillow, tải qua yt-dlp/aria2...).
- Xử lý lỗi và thông báo bằng tiếng Việt; thoát bằng `sys.exit(0)` khi thành công hoặc `sys.exit(1)` khi có lỗi.

### Bước 2: Khai báo Hằng Số & Handler trong `src/main.py`
- Khai báo hằng số type/action (vd: `MDIA_TYPE_<NAME>`, `MDIA_<NAME>_ACTION_<ACTION>`).
- Viết hàm `run_<name>_<action>(...)`:
  ```python
  def run_new_feature(input_path: str, opt: str):
      if not input_path:
          raise Exception(f"{MDIA_WARNING_ACTION_MISSING} - Cần truyền input_path")
      script_path = get_script_path("features/<module>/<script>.py")
      cmd = [sys.executable, script_path, input_path]
      if opt:
          cmd.extend(["--opt", opt])
      subprocess.run(cmd)
      sys.exit(0)
  ```
- Bổ sung cấu hình cờ (flags) trong `argparse` của `main()` nếu có thêm flag mới.
- Thêm nhánh routing tương ứng trong khối Dispatcher `main()`.

### Bước 3: Đăng ký Autocomplete trong `src/utils/interactive_cli.py`
- Cập nhật `TYPE_ACTION_MAP`: Thêm `action` vào mảng của `type` tương ứng (luôn giữ thứ tự **sắp xếp A-Z**). Nếu là Type mới, thêm key mới kèm mảng actions.
- Cập nhật `TYPE_DESCRIPTIONS`: Thêm hoặc cập nhật dòng mô tả tóm tắt tiếng Việt cho Type.

### Bước 4: Đồng bộ tài liệu 3 lớp
- [`src/contents/help.txt`](file:///d:/D-Documents/TOOLs/media-studio/src/contents/help.txt): Bổ sung định nghĩa action và ví dụ mẫu `// Vd: mda <type> <action> ...`.
- [`src/contents/app_features.yml`](file:///d:/D-Documents/TOOLs/media-studio/src/contents/app_features.yml): Khai báo block YAML (ID, title, command, summary, details, parameters, flags, conditions) phục vụ cờ `--des`.
- [`PROJECT_CONTEXT.md`](file:///d:/D-Documents/TOOLs/media-studio/PROJECT_CONTEXT.md): Cập nhật cây thư mục và Bảng tra cứu Type & Action tại Mục 3.2.
- [`README.md`](file:///d:/D-Documents/TOOLs/media-studio/README.md): Bổ sung hướng dẫn ngắn gọn cho người dùng.

### Bước 5: Kiểm thử bắt buộc (Verification)
1. `python src/main.py <type> <action> --des` $\rightarrow$ Phải in ra đúng mô tả catalog YAML.
2. Kiểm tra Tab Autocomplete trong Chế độ Tương tác (`python src/main.py` -> gõ prefix + Tab).
3. Kiểm thử cú pháp toàn dự án: `python -m compileall -q src`.
4. Chạy lệnh thực thi thực tế kiểm tra kết quả output.

---

## 3. SOP 2: Quy Trình CHỈNH SỬA Tính Năng (Edit Feature)

Khi chỉnh sửa một tính năng đã tồn tại:

1. **Trường hợp sửa logic nội bộ:** Chỉ sửa file script tương ứng trong `src/features/` hoặc `src/utils/`.
2. **Trường hợp thay đổi cú pháp / tham số / cờ:**
   - Cập nhật script trong `src/features/`.
   - Cập nhật hàm handler `run_*` và cấu hình parser trong `src/main.py`.
   - Cập nhật nội dung giải thích và ví dụ trong `src/contents/help.txt`.
   - Cập nhật `command`, `summary`, `details`, `flags` trong `src/contents/app_features.yml`.
   - Cập nhật lại dòng mô tả trong `PROJECT_CONTEXT.md` và `README.md`.
3. **Kiểm thử lại:** Chạy lệnh `--des`, biên dịch `python -m compileall -q src` và test thực thi.

---

## 4. SOP 3: Quy Trình XÓA Tính Năng (Delete Feature)

Khi xóa bỏ hoàn toàn một lệnh hoặc một nhóm lệnh:

1. **Xóa Script:** Xóa file script liên quan trong `src/features/` (nếu không còn action nào khác dùng chung).
2. **Dọn dẹp `src/main.py`:**
   - Xóa hằng số `MDIA_*` của type/action bị xóa.
   - Xóa hàm handler `run_*`.
   - Xóa nhánh `elif cmd_action == ...` hoặc `elif cmd_type == ...` trong `main()`.
3. **Dọn dẹp Autocomplete:**
   - Gỡ bỏ action hoặc type khỏi `TYPE_ACTION_MAP` và `TYPE_DESCRIPTIONS` trong `src/utils/interactive_cli.py`.
4. **Dọn dẹp Tài Liệu:**
   - Xóa mục tương ứng trong `src/contents/help.txt`.
   - Xóa block action trong `src/contents/app_features.yml`.
   - Xóa khỏi bảng tra cứu trong `PROJECT_CONTEXT.md` và `README.md`.
5. **Kiểm thử hồi quy:** Chạy `python src/main.py` kiểm tra danh mục Type sạch sẽ và biên dịch không phát sinh lỗi cú pháp.

---

## 5. Danh Mục File Bản Đồ (File Map Reference)

| File | Vai trò | Khi nào cần sửa? |
| :--- | :--- | :--- |
| `src/main.py` | Central Dispatcher | Thêm/sửa/xóa Type hoặc Action, thêm cờ mới |
| `src/configs/paths.py` | Central Paths Config | Thêm thư mục/file cấu hình trung tâm mới |
| `src/utils/helpers.py` | Helpers & URL Sanitizer | Xử lý file/path helpers, chuẩn hóa URL downloader |
| `src/utils/interactive_cli.py` | REPL & Tab Autocomplete | Thêm/sửa/xóa Type hoặc Action trong autocomplete |
| `src/contents/help.txt` | Text Help Guide | Thêm/sửa/xóa Type hoặc Action |
| `src/contents/app_features.yml` | Catalog cho cờ `--des` | Thêm/sửa/xóa Type hoặc Action |
| `PROJECT_CONTEXT.md` | Master Context cho AI Agent | Luôn luôn cập nhật đồng bộ sau mọi thay đổi |
| `README.md` | Hướng dẫn người dùng | Cập nhật khi thay đổi cú pháp hoặc tính năng lớn |
