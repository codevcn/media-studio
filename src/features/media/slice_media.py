import os
import sys
import subprocess
import re
from pathlib import Path

def validate_time_format(time_str: str) -> bool:
    """
    Kiểm tra định dạng thời gian hợp lệ: MM:SS hoặc HH:MM:SS
    """
    pattern = r'^(\d{2}:)?\d{2}:\d{2}$'
    return bool(re.match(pattern, time_str))

def time_to_seconds(time_str: str) -> int:
    """
    Chuyển đổi chuỗi thời gian (MM:SS hoặc HH:MM:SS) sang giây
    """
    parts = time_str.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + int(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + int(s)
    return 0

def slice_media(input_path: str, time_range: str, output_filename: str | None = None):
    # 1. Kiểm tra file đầu vào
    if not os.path.exists(input_path):
        print(f">>> Lỗi: Không tìm thấy file đầu vào '{input_path}'")
        sys.exit(1)
        
    # Check extension to prevent image slicing
    ext = Path(input_path).suffix.lower()
    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}
    if ext in image_exts:
        print(f">>> Lỗi: Tính năng slice không hỗ trợ cắt hình ảnh ({ext}). Chỉ dùng cho video/audio.")
        sys.exit(1)

    # 2. Kiểm tra định dạng time_range
    if "-" not in time_range:
        print(">>> Lỗi: time_range phải chứa dấu '-' phân cách (vd: 00:10-01:22)")
        sys.exit(1)
        
    start_time, end_time = time_range.split("-", 1)
    
    if not validate_time_format(start_time) or not validate_time_format(end_time):
        print(">>> Lỗi: Định dạng thời gian không hợp lệ. Vui lòng dùng MM:SS hoặc HH:MM:SS (vd: 00:10-01:22 hoặc 02:00:11-03:01:22)")
        sys.exit(1)

    # 3. Kiểm tra tính hợp lý của thời gian
    start_sec = time_to_seconds(start_time)
    end_sec = time_to_seconds(end_time)
    
    if start_sec >= end_sec:
        print(f">>> Lỗi: Thời gian kết thúc ({end_time}) phải lớn hơn thời gian bắt đầu ({start_time}).")
        sys.exit(1)

    # 4. Tạo output path
    input_p = Path(input_path)
    output_dir = input_p.parent
    
    if output_filename:
        # Nếu user truyền filename, xài filename đó nhưng giữ nguyên phần mở rộng của file gốc nếu user không truyền .ext
        if not Path(output_filename).suffix:
            output_name = f"{output_filename}{ext}"
        else:
            output_name = output_filename
    else:
        # Mặc định thêm hậu tố time_range vào tên file
        safe_time = time_range.replace(":", "")
        output_name = f"{input_p.stem}_slice_{safe_time}{ext}"
        
    output_path = output_dir / output_name

    print(f">>> Đang tiến hành cắt file từ {start_time} đến {end_time}...")
    print(f">>> File đích: {output_path}")

    # 5. Thực thi FFmpeg
    # Sử dụng stream copy (-c copy) để cắt siêu tốc mà không encode lại.
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ss", start_time,
        "-to", end_time,
        "-c", "copy",
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        print("-" * 50)
        print(">>> Hoàn tất! File đã được cắt thành công.")
    except subprocess.CalledProcessError as e:
        print("-" * 50)
        print(">>> LỖI FFmpeg:")
        print(e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(">>> Lỗi: Hệ thống không tìm thấy phần mềm 'ffmpeg'. Hãy chắc chắn bạn đã cài đặt FFmpeg và cấu hình PATH.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Sử dụng: python slice_media.py <input_path> <time_range> [output_filename]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    t_range = sys.argv[2]
    out_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    slice_media(input_file, t_range, out_name)
