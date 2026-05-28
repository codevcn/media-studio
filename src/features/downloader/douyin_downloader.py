#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path
import os
import yaml
from dotenv import load_dotenv

# Ensure src directory is in sys.path
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from configs.paths import ROOT_FOLDER_PATH

env_path = os.path.join(ROOT_FOLDER_PATH, ".env")
load_dotenv(dotenv_path=env_path)

# Đường dẫn tuyệt đối của thư mục douyin-downloader
DOUYIN_DOWNLOADER_DIR = (
    Path(ROOT_FOLDER_PATH) / "src" / "external" / "douyin-downloader"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tải media từ Douyin bằng jiji262/douyin-downloader"
    )
    parser.add_argument(
        "url", nargs="?", help="URL Douyin (video/profile/collection...)"
    )
    parser.add_argument(
        "--config", "-c", default="config.yml", help="Đường dẫn config.yml"
    )
    parser.add_argument(
        "--folder",
        "-p",
        default=os.getcwd(),
        help="Thư mục lưu (mặc định: current working directory)",
    )
    parser.add_argument(
        "--mode",
        choices=["post", "like", "mix", "music", "favorites"],
        help="Chế độ batch",
    )
    parser.add_argument("--threads", "-t", type=int, default=5, help="Số luồng tải")
    parser.add_argument("--des", action="store_true", help="Hiển thị mô tả chi tiết")
    parser.add_argument("--noti", type=str, default=None, help="Gửi thông báo")
    return parser.parse_args()


def main():
    # Cấu hình UTF-8 cho console Windows
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    if args.des:
        print(
            "Tích hợp douyin-downloader: hỗ trợ single/batch download Douyin chuyên sâu (no-watermark, deduplication, browser fallback)."
        )
        sys.exit(0)

    if not args.url:
        print("Lỗi: Vui lòng cung cấp URL Douyin.")
        sys.exit(1)

    cmd = [
        sys.executable,
        str(DOUYIN_DOWNLOADER_DIR / "run.py"),
        "-c",
        str(DOUYIN_DOWNLOADER_DIR / args.config),
        "-u",
        args.url,
        "-p",
        args.folder,
        "-t",
        str(args.threads),
    ]
    if args.mode:
        cmd.extend(["--mode", args.mode])

    result = subprocess.run(cmd, cwd=DOUYIN_DOWNLOADER_DIR, check=False)

    if result.returncode == 0 and args.noti:
        from utils.notifiers import NotifierFactory

        notifier = NotifierFactory.get_notifier(args.noti)
        if notifier:
            notifier.notify(f"✅ Đã tải xong Douyin URL:\n{args.url}")

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
