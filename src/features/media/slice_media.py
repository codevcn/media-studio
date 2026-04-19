"""
Slice a WAV, MP3, or MP4 file into chunks of specified MB using ffmpeg.
Usage: python slice_audio.py <input_file> <size_mb>
"""

import os
import sys
import subprocess
import json
import datetime

SUPPORTED_FORMATS = (".wav", ".mp3", ".mp4")


def get_media_info(input_file: str) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        input_file,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    fmt = data["format"]
    return {
        "duration": float(fmt["duration"]),
        "size": int(fmt["size"]),
    }


def slice_file(input_file: str, target_size_mb: float) -> None:
    # --- Validate file tồn tại ---
    if not os.path.isfile(input_file):
        print(f"[ERROR] File not found: {input_file}")
        sys.exit(1)

    # --- Validate định dạng ---
    ext = os.path.splitext(input_file)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        supported = ", ".join(SUPPORTED_FORMATS)
        print(f"[ERROR] Unsupported format '{ext}'.")
        print(f"        Supported formats: {supported}")
        sys.exit(1)

    target_size_bytes = target_size_mb * 1024 * 1024
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    input_dir = os.path.dirname(os.path.abspath(input_file))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{base_name}-{timestamp}"
    output_dir = os.path.join(input_dir, folder_name)

    os.makedirs(output_dir, exist_ok=True)

    print(f"[INFO] Input     : {input_file}")
    print(f"[INFO] Format    : {ext}")
    print(f"[INFO] Chunk size: {target_size_mb} MB")

    info = get_media_info(input_file)
    total_duration = info["duration"]
    total_size = info["size"]

    print(f"[INFO] Duration  : {total_duration:.2f}s")
    print(f"[INFO] File size : {total_size / 1024 / 1024:.2f} MB")

    if total_size <= target_size_bytes:
        print(f"[INFO] File is already <= {target_size_mb} MB. No slicing needed.")
        return

    # Tính chunk duration theo tỉ lệ byte/giây, thêm margin nhỏ để không vượt target
    bytes_per_second = total_size / total_duration
    chunk_duration = (target_size_bytes / bytes_per_second) * 0.995

    print(f"[INFO] Chunk duration: {chunk_duration:.2f}s\n")

    start = 0.0
    part = 1
    output_files = []

    while start < total_duration:
        duration = min(chunk_duration, total_duration - start)
        output_file = os.path.join(output_dir, f"{base_name}_part{part:03d}{ext}")

        print(f"[INFO] Part {part:03d}: {start:.2f}s → {start + duration:.2f}s")
        print(f"         Output: {output_file}")

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_file,
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-c",
            "copy",  # stream copy: không re-encode, nhanh và không mất chất lượng
            output_file,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ERROR] ffmpeg failed on part {part}:\n{result.stderr}")
            sys.exit(1)

        actual_size = os.path.getsize(output_file)
        print(f"         Size  : {actual_size / 1024 / 1024:.2f} MB")
        output_files.append(output_file)

        start += duration
        part += 1

    print(f"\n[DONE] Created {len(output_files)} file(s):")
    for f in output_files:
        print(f"  {f}  ({os.path.getsize(f) / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage  : python slice_audio.py <input_file> <size_mb>")
        print("Example: python slice_audio.py audio.wav 48")
        print(f"Formats: {', '.join(SUPPORTED_FORMATS)}")
        sys.exit(1)

    input_file = sys.argv[1]

    try:
        size_mb = float(sys.argv[2])
        if size_mb <= 0:
            raise ValueError
    except ValueError:
        print("[ERROR] <size_mb> must be a positive number.")
        sys.exit(1)

    slice_file(input_file, size_mb)
