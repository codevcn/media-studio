import subprocess
from pathlib import Path
import sys


def print_usage() -> None:
    script_name = Path(sys.argv[0]).name
    print("Hướng dẫn dùng lệnh:")
    print(f'  {script_name} "ABSOLUTE_INPUT_VIDEO_PATH" "ABSOLUTE_OUTPUT_AUDIO_PATH"')
    print()
    print("Ví dụ WAV:")
    print(f'  {script_name} "D:\\data\\video.mp4" "D:\\data\\output.wav"')
    print()
    print("Ví dụ MP3:")
    print(f'  {script_name} "D:\\data\\video.mp4" "D:\\data\\output.mp3"')
    print()


def build_ffmpeg_cmd(input_path: Path, output_path: Path) -> list[str]:
    suffix = output_path.suffix.lower()

    if suffix == ".wav":
        return [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            str(output_path),
        ]

    if suffix == ".mp3":
        return [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-acodec",
            "libmp3lame",
            "-q:a",
            "2",
            str(output_path),
        ]

    raise ValueError("Output audio file phải có đuôi .wav hoặc .mp3")


def extract_audio(input_video_path: str, output_audio_path: str) -> Path:
    input_path = Path(input_video_path)
    output_path = Path(output_audio_path)

    if not input_path.is_absolute():
        raise ValueError(f"Input path không phải absolute path: {input_path}")

    if not output_path.is_absolute():
        raise ValueError(f"Output path không phải absolute path: {output_path}")

    if not input_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file video đầu vào: {input_path}")

    if input_path.is_dir():
        raise ValueError(
            f"Input path phải là file video, không phải thư mục: {input_path}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_cmd = build_ffmpeg_cmd(input_path, output_path)

    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        print(f"Tách audio thành công: {output_path}")
        return output_path

    except FileNotFoundError:
        raise RuntimeError(
            "Không tìm thấy ffmpeg hoặc python. Hãy kiểm tra PATH trên Windows."
        )

    except subprocess.CalledProcessError as e:
        print("ffmpeg stderr:")
        print(e.stderr)
        raise RuntimeError("Tách audio thất bại.") from e


if __name__ == "__main__":
    print_usage()

    if len(sys.argv) != 3:
        print("Lỗi: cần đúng 2 tham số.")
        sys.exit(1)

    input_video = sys.argv[1]
    output_audio = sys.argv[2]

    extract_audio(input_video, output_audio)
