# Media Studio CLI Development Checklists

---

## 🟢 Checklist 1: THÊM TÍNH NĂNG MỚI (Add Feature)
- [ ] **Feature Script (`src/features/<module>/<script>.py`)**:
  - [ ] Cấu hình `sys.path.insert(0, src_dir)` và import `ROOT_FOLDER_PATH` từ `configs.paths`.
  - [ ] Gọi `ensure_utf8_stdout()` với `sys.stdout.reconfigure(encoding="utf-8")`.
  - [ ] Parse `sys.argv` an toàn bằng `argparse` hoặc positional args, validate file tồn tại.
  - [ ] Nếu là tính năng nhận URL: Gọi `clean_url(url, platform)` từ `utils.helpers`.
  - [ ] Thoát đúng `sys.exit(0)` khi thành công và `sys.exit(1)` khi có lỗi.
- [ ] **Central Dispatcher (`src/main.py`)**:
  - [ ] Khai báo hằng số `MDIA_TYPE_*` (nếu là type mới) và `MDIA_<TYPE>_ACTION_*`.
  - [ ] Khai báo hàm handler `run_<type>_<action>(...)` gọi `get_script_path(...)` và `subprocess.run(...)`.
  - [ ] Thêm cờ mới vào `argparse` của `main()` nếu cần.
  - [ ] Bổ sung nhánh định tuyến trong khối Dispatcher `main()`.
- [ ] **Tab Autocomplete (`src/utils/interactive_cli.py`)**:
  - [ ] Cập nhật `TYPE_ACTION_MAP`: Bổ sung action vào mảng tương ứng (luôn giữ thứ tự **sắp xếp A-Z**).
  - [ ] Cập nhật `TYPE_DESCRIPTIONS`: Thêm hoặc cập nhật dòng mô tả tiếng Việt.
- [ ] **Đồng bộ tài liệu 4 lớp**:
  - [ ] `src/contents/help.txt` (thêm cú pháp và ví dụ `// Vd: mda ...`).
  - [ ] `src/contents/app_features.yml` (chuẩn bị block YAML cho cờ `--info`).
  - [ ] `PROJECT_CONTEXT.md` (cây thư mục & bảng tra cứu Type / Action tại mục 3.2).
  - [ ] `README.md` (hướng dẫn cho người dùng cuối).
- [ ] **Kiểm thử nghiệm thu**:
  - [ ] `python src/main.py <type> <action> --info` $\rightarrow$ In đúng format YAML.
  - [ ] Kiểm tra Tab Autocomplete trong Chế độ Tương tác (`python src/main.py`).
  - [ ] `python -m compileall -q src` $\rightarrow$ Đạt mã thoát 0.
  - [ ] Chạy lệnh trực tiếp với dữ liệu mẫu trong `data/`.

---

## 🟡 Checklist 2: CHỈNH SỬA TÍNH NĂNG (Edit Feature)
- [ ] Cập nhật mã nguồn trong `src/features/<module>/<script>.py`.
- [ ] Kiểm tra xem có đổi cờ/đối số hay không $\rightarrow$ Nếu có, cập nhật lại parser và hàm `run_*` trong `src/main.py`.
- [ ] Cập nhật mô tả & ví dụ trong `src/contents/help.txt`.
- [ ] Cập nhật trường `command`, `summary`, `details`, `flags` trong `src/contents/app_features.yml`.
- [ ] Cập nhật bảng tra cứu lệnh trong `PROJECT_CONTEXT.md` và `README.md`.
- [ ] Chạy lệnh kiểm thử `--info`, biên dịch `compileall` và chạy lệnh thực thi.

---

## 🔴 Checklist 3: XÓA TÍNH NĂNG (Delete Feature)
- [ ] Xóa file script trong `src/features/<module>/`.
- [ ] Gỡ bỏ hằng số `MDIA_*`, hàm handler `run_*` và nhánh routing trong `src/main.py`.
- [ ] Gỡ bỏ khỏi `TYPE_ACTION_MAP` và `TYPE_DESCRIPTIONS` trong `src/utils/interactive_cli.py`.
- [ ] Xóa mục tương ứng trong `src/contents/help.txt`.
- [ ] Xóa block YAML trong `src/contents/app_features.yml`.
- [ ] Xóa khỏi `PROJECT_CONTEXT.md` và `README.md`.
- [ ] Kiểm thử: Chạy `mda` kiểm tra menu Type sạch sẽ và `python -m compileall -q src` không phát sinh lỗi.
