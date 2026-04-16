import json
import shutil
import subprocess
import sys
from pathlib import Path


def extract_video_metadata(video_path: str, output_json: str | None = None) -> dict:
    """
    Đọc metadata của video bằng ffprobe.
    - video_path: đường dẫn tới file video
    - output_json: nếu có, sẽ lưu metadata ra file JSON
    """
    video_file = Path(video_path)

    if not video_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {video_file}")

    if shutil.which("ffprobe") is None:
        raise EnvironmentError(
            "Không tìm thấy ffprobe trong PATH. "
            "Hãy cài FFmpeg và thêm ffprobe vào biến môi trường PATH."
        )

    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_file),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )

    metadata = json.loads(result.stdout)

    if output_json:
        output_file = Path(output_json)
        output_file.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    return metadata


if __name__ == "__main__":
    video_path = "D:/D-Jobs/ae-B6/TikTok-Beta/coding/src/data/media/videoplayback.mp4"
    output_json = "D:/D-Jobs/ae-B6/TikTok-Beta/coding/src/data/media/videoplayback.json"

    try:
        metadata = extract_video_metadata(video_path, output_json)

        print("=== TOÀN BỘ METADATA ===")
        print(json.dumps(metadata, indent=2, ensure_ascii=False))

        print(f"\nĐã lưu metadata vào: {output_json}")

    except subprocess.CalledProcessError as e:
        print("Lỗi khi chạy ffprobe:")
        print(e.stderr or str(e))
    except Exception as e:
        print(f"Lỗi: {e}")
