"""
Slice a media file into chunks of specified duration using ffmpeg segment muxer.
Usage: python part_media.py <input_file> <duration>
Duration can be in seconds (e.g. 20s) or minutes (e.g. 3p, 3m).
"""

import os
import sys
import subprocess
import datetime
import re

SUPPORTED_FORMATS = (".wav", ".mp3", ".mp4", ".mkv", ".mov", ".flv", ".aac")


def parse_duration(duration_str: str) -> float:
    duration_str = duration_str.strip().lower()
    if duration_str.endswith("s"):
        return float(duration_str[:-1])
    elif duration_str.endswith("p") or duration_str.endswith("m"):
        return float(duration_str[:-1]) * 60
    elif duration_str.endswith("h"):
        return float(duration_str[:-1]) * 3600
    else:
        # If no unit, assume seconds
        try:
            return float(duration_str)
        except ValueError:
            raise ValueError(f"Không thể phân tích giá trị thời gian: '{duration_str}'")


def part_media(input_file: str, duration_str: str, limit: int = 0) -> None:
    # --- Validate file tồn tại ---
    if not os.path.isfile(input_file):
        print(f"[ERROR] Không tìm thấy file: {input_file}")
        sys.exit(1)

    # --- Validate định dạng ---
    ext = os.path.splitext(input_file)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        supported = ", ".join(SUPPORTED_FORMATS)
        print(f"[ERROR] Định dạng không được hỗ trợ '{ext}'.")
        print(f"        Các định dạng hỗ trợ: {supported}")
        sys.exit(1)

    # --- Parse duration ---
    try:
        duration_sec = parse_duration(duration_str)
        if duration_sec <= 0:
            raise ValueError("Duration must be > 0")
    except Exception as e:
        print(f"[ERROR] Thời gian không hợp lệ: {duration_str}")
        print("        Ví dụ hợp lệ: 20s, 3p, 3m")
        sys.exit(1)

    # --- Tạo Output Folder ---
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    input_dir = os.path.dirname(os.path.abspath(input_file))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{base_name}--part--{timestamp}"
    output_dir = os.path.join(input_dir, folder_name)

    os.makedirs(output_dir, exist_ok=True)

    # --- Gọi FFmpeg để segment stream copy ---
    # File name pattern: part_000.mp4, part_001.mp4...
    output_pattern = os.path.join(output_dir, f"part_%03d{ext}")

    print(f"[INFO] Input          : {input_file}")
    print(f"[INFO] Thời gian cắt  : {duration_sec}s mỗi phần")
    print(f"[INFO] Thư mục output : {output_dir}")

    cmd = [
        "ffmpeg",
        "-y",  # Ghi đè nếu có
        "-i",
        input_file,
    ]

    if limit > 0:
        max_duration = duration_sec * limit
        cmd.extend(["-t", str(max_duration)])
        print(
            f"[INFO] Giới hạn kết quả: {limit} file (Tổng thời lượng: {max_duration}s)"
        )

    cmd.extend(
        [
            "-c",
            "copy",  # Stream copy
            "-map",
            "0",  # Map tất cả streams (audio, video, subs)
            "-f",
            "segment",
            "-segment_time",
            str(duration_sec),
            "-reset_timestamps",
            "1",
            output_pattern,
        ]
    )

    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print(f"[ERROR] ffmpeg failed:\n{result.stderr}")
        sys.exit(1)

    # Liệt kê kết quả
    files_created = sorted([f for f in os.listdir(output_dir) if f.endswith(ext)])
    print(f"\n[DONE] Đã tạo thành công {len(files_created)} file(s):")
    for f in files_created:
        full_p = os.path.join(output_dir, f)
        size_mb = os.path.getsize(full_p) / (1024 * 1024)
        print(f"  {f}  ({size_mb:.2f} MB)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage  : python part_media.py <input_file> <duration_string> [limit]")
        print("Example: python part_media.py video.mp4 20s 5")
        print("         python part_media.py audio.mp3 3p")
        sys.exit(1)

    input_file = sys.argv[1]
    duration_str = sys.argv[2]

    limit_val = 0
    if len(sys.argv) >= 4:
        try:
            limit_val = int(sys.argv[3])
        except ValueError:
            pass

    part_media(input_file, duration_str, limit_val)
