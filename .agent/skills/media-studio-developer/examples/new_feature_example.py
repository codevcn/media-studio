"""
Feature Script Template mẫu chuẩn mực dành cho Media Studio CLI (mda).
"""
import os
import sys
import argparse
from pathlib import Path

# Đảm bảo src directory nằm trong sys.path để import configs / utils
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from configs.paths import ROOT_FOLDER_PATH


def ensure_utf8_stdout():
    """Đảm bảo console Windows in tiếng Việt UTF-8 không lỗi font."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")


def execute_feature(input_path: str, output_path: str | None = None, option: str = "default"):
    """
    Hàm thực thi nghiệp vụ cốt lõi (xử lý FFmpeg / Pillow / Media / OCR / Download).
    """
    ensure_utf8_stdout()
    
    if not os.path.exists(input_path):
        print(f">>> [LỖI] File đầu vào không tồn tại: {input_path}")
        sys.exit(1)

    print(f"[*] Đang xử lý: {input_path}")
    print(f"[*] Tùy chọn: {option}")

    # Xây dựng đường dẫn output nếu chưa được chỉ định
    if not output_path:
        stem = Path(input_path).stem
        ext = Path(input_path).suffix
        output_path = os.path.join(ROOT_FOLDER_PATH, "data", "video", "output", f"{stem}_processed{ext}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    print(f"[*] File kết quả sẽ lưu tại: {output_path}")

    # TODO: Thực hiện gọi FFmpeg / logic xử lý tại đây
    # Ví dụ: subprocess.run(["ffmpeg", "-i", input_path, ...], check=True)

    print(">>> [THÀNH CÔNG] Đã hoàn tất xử lý!")
    sys.exit(0)


def main():
    ensure_utf8_stdout()

    parser = argparse.ArgumentParser(description="Template Feature Script cho Media Studio")
    parser.add_argument("input_path", type=str, help="Đường dẫn file media đầu vào")
    parser.add_argument("--output", "-o", type=str, default=None, help="Đường dẫn file đầu ra")
    parser.add_argument("--option", type=str, default="default", help="Tùy chọn xử lý")

    args = parser.parse_args()
    execute_feature(args.input_path, args.output, args.option)


if __name__ == "__main__":
    main()
