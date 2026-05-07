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
DOUYIN_DOWNLOADER_DIR = Path(ROOT_FOLDER_PATH) / "src" / "external" / "douyin-downloader"

def parse_args():
    parser = argparse.ArgumentParser(description="Tải media từ Douyin bằng jiji262/douyin-downloader")
    parser.add_argument("url", nargs="?", help="URL Douyin (video/profile/collection...)")
    parser.add_argument("--config", "-c", default="config.yml", help="Đường dẫn config.yml")
    parser.add_argument("--folder", "-p", default=os.getcwd(), help="Thư mục lưu (mặc định: current working directory)")
    parser.add_argument("--mode", choices=["post", "like", "mix", "music", "favorites"], help="Chế độ batch")
    parser.add_argument("--threads", "-t", type=int, default=5, help="Số luồng tải")
    parser.add_argument("--des", action="store_true", help="Hiển thị mô tả chi tiết")
    return parser.parse_args()

def main():
    # Cấu hình UTF-8 cho console Windows
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    if args.des:
        print("Tích hợp douyin-downloader: hỗ trợ single/batch download Douyin chuyên sâu (no-watermark, deduplication, browser fallback).")
        sys.exit(0)

    if not args.url:
        print("Lỗi: Vui lòng cung cấp URL Douyin.")
        sys.exit(1)

    cmd = [
        sys.executable, str(DOUYIN_DOWNLOADER_DIR / "run.py"),
        "-c", str(DOUYIN_DOWNLOADER_DIR / args.config),
        "-u", args.url,
        "-p", args.folder,
        "-t", str(args.threads)
    ]
    if args.mode:
        cmd.extend(["--mode", args.mode])

    msToken = os.getenv("DOUYIN_MS_TOKEN", "")
    ttwid = os.getenv("DOUYIN_TTWID", "")
    odin_tt = os.getenv("DOUYIN_ODIN_TT", "")
    csrf_token = os.getenv("DOUYIN_PASSPORT_CSRF_TOKEN", "")
    sid_guard = os.getenv("DOUYIN_SID_GUARD", "")

    if not msToken or not ttwid or not odin_tt or not csrf_token or not sid_guard:
        print(">>> LỖI: Chưa cấu hình đủ 5 biến Cookie Douyin trong file .env!")
        print("Douyin hiện tại chặn các yêu cầu tải ẩn danh (không có cookie hợp lệ).")
        print("Vui lòng mở trình duyệt (đã đăng nhập Douyin), nhấn F12 -> Application -> Storage -> Cookies.")
        print("Tìm và copy các giá trị tương ứng vào file .env:")
        print("- DOUYIN_MS_TOKEN")
        print("- DOUYIN_TTWID")
        print("- DOUYIN_ODIN_TT")
        print("- DOUYIN_PASSPORT_CSRF_TOKEN")
        print("- DOUYIN_SID_GUARD")
        sys.exit(1)

    config_path = DOUYIN_DOWNLOADER_DIR / args.config
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        
        if "cookies" not in config_data or not isinstance(config_data["cookies"], dict):
            config_data["cookies"] = {}
            
        config_data["cookies"]["msToken"] = msToken
        config_data["cookies"]["ttwid"] = ttwid
        config_data["cookies"]["odin_tt"] = odin_tt
        config_data["cookies"]["passport_csrf_token"] = csrf_token
        config_data["cookies"]["sid_guard"] = sid_guard

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        print(f">>> Lỗi cập nhật cookie vào config.yml: {e}")
        sys.exit(1)

    result = subprocess.run(cmd, cwd=DOUYIN_DOWNLOADER_DIR, check=False)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
