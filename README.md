# Media Studio CLI (mda)

Media Studio là một tập hợp các công cụ dòng lệnh (CLI) và ứng dụng GUI mạnh mẽ chuyên dùng để xử lý video, âm thanh, và hình ảnh.

## 🚀 Tính năng nổi bật

### 1. Ứng dụng GUI: Trình phát Video Kép

- Lệnh: `mda app player`
- Giao diện người dùng được xây dựng bằng PySide6 cho phép so sánh song song hai video (ví dụ: video gốc và video đã xử lý).
- Hỗ trợ cuộn danh sách (sidebar) các cặp video tự động phát hiện trong thư mục dữ liệu, cùng tổ hợp phím tắt đa dạng để dễ dàng theo dõi.

### 2. Xử lý Video

- **Xóa Watermark/Logo (`mda video rm-logo`)**: Sử dụng công nghệ xử lý của FFmpeg để xóa logo hoặc watermark trên video dựa vào tọa độ chính xác.
- **Trích xuất Khung hình (`mda video frames`)**: Bóc tách video ra dưới dạng chuỗi các ảnh PNG chất lượng cao (lossless) theo khoảng giãn cách cố định (ví dụ: 100ms, 2s).

### 3. Xử lý Âm Thanh

- **Tách Audio (`mda audio extract`)**: Tách nhanh âm thanh ra khỏi video và lưu trữ dưới định dạng `WAV` (không suy hao) hoặc `MP3` chất lượng.

### 4. Chia nhỏ Media (Video / Audio) - Xử lý cực nhanh

- **Chia theo dung lượng (`mda media part-size`)**: Tự động tính toán bitrate để chia nhỏ một tệp media thành các phần con với kích thước (MB) sát với yêu cầu nhất. Quá trình chia thực hiện thông qua Stream Copy không encode lại, vì vậy hoạt động với tốc độ chớp nhoáng.
- **Chia theo thời lượng (`mda media part-time`)**: Cắt liên hoàn tệp dài thành các đoạn với thời lượng cho trước (ví dụ: 30s/phần).

### 5. Tải xuống đa nền tảng (Downloader)

- **Tải Video/Audio (`mda dld <platform>`)**: Hỗ trợ tải nội dung đa phương tiện từ YouTube, YouTube Music, Facebook, Instagram, TikTok, Douyin, Bilibili bằng `yt-dlp`.
- Cung cấp tùy chọn tải linh hoạt: chất lượng cao nhất (`best-vid`), chất lượng khá (`good-vid`), chỉ âm thanh (`audio`), hoặc chỉ tải phụ đề (`sub`).
- Nếu không truyền tùy chọn sau URL, mặc định dùng `good-vid`; vẫn hỗ trợ tuỳ chỉnh tên file (`--filename`) và thư mục đích (`--folder`).
- Tăng tốc tải bằng `aria2c`; dùng `--threads` hoặc `--aria2-threads` để chỉnh số luồng tải song song, mặc định là `4`.
- Hỗ trợ cookie cho các nền tảng yêu cầu xác minh qua `--cookies-from-browser chrome|edge|firefox` hoặc `--cookies <cookies.txt>`; riêng Douyin sẽ tự thử cookies từ `chrome`, `edge`, `firefox` nếu bạn không truyền cookie thủ công.

### 6. Tiện ích Phụ Trợ

- Lật ảnh ngang/dọc qua lệnh `mda image flip <absolute_input_path> <horizontal|vertical> [output_path]`.
- Mở nhanh Workspace trong Editor qua lệnh `mda open`.
- Tự động hóa quá trình đóng gói Git qua lệnh `mda git commit`.

## 🛠 Yêu cầu hệ thống

- **Python 3.x**: Đã cài đặt các thư viện trong danh sách `requirements.txt`.
- **FFmpeg**: Yêu cầu bắt buộc cài đặt và trỏ biến môi trường `PATH` nhằm thực hiện mọi thao tác giải mã/mã hóa đa phương tiện.
- **aria2**: Cần có lệnh `aria2c` trong `PATH` để tăng tốc tải xuống cho nhóm lệnh `dld`.

## 📁 Cấu trúc lưu trữ dữ liệu

Theo chuẩn mực, bạn nên copy các tệp đa phương tiện (video đầu vào, kết quả xuất) vào hai thư mục sau:

- Thư mục Input: `src/data/media/input/`
- Thư mục Output: `src/data/media/output/`

## 💡 Tra cứu Thêm

Sử dụng cờ `--des` kết hợp khai báo tham số loại tác vụ để tra cứu thông tin chi tiết các tham số cần thiết khi chạy. Ví dụ:

```bash
mda --des
mda --help
```
