import sys
import argparse

# Cho phép import các file cùng cấp
from platform_downloaders import (
    YoutubeDownloader,
    YoutubeMusicDownloader,
    FacebookDownloader,
    InstagramDownloader,
    TiktokDownloader,
)


def main():
    # Cấu hình UTF-8 cho console Windows để in được tiếng Việt
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Media Studio Downloader Module")
    parser.add_argument(
        "platform", type=str, help="Nền tảng (ytb, ytb-music, fb, insta, tiktok)"
    )
    parser.add_argument("url", type=str, help="URL video cần tải")
    parser.add_argument(
        "option", type=str, help="Tùy chọn tải: best-vid, good-vid, audio, sub"
    )
    parser.add_argument("--filename", type=str, default=None, help="Tên file đầu ra")
    parser.add_argument("--folder", type=str, default=None, help="Thư mục lưu trữ")
    parser.add_argument("--format", type=str, default=None, help="Định dạng file tải xuống (mp4, mp3, wav...)")

    args = parser.parse_args()

    platform = args.platform.lower()
    url = args.url
    option = args.option
    filename = args.filename
    folder = args.folder
    format_ext = args.format

    # Map platform code tới các Class tương ứng
    downloaders_map = {
        "ytb": YoutubeDownloader,
        "ytb-music": YoutubeMusicDownloader,
        "fb": FacebookDownloader,
        "insta": InstagramDownloader,
        "tiktok": TiktokDownloader,
    }

    if platform not in downloaders_map:
        print(f">>> Lỗi: Nền tảng '{platform}' không được hỗ trợ.")
        print(f"Các nền tảng hợp lệ: {', '.join(downloaders_map.keys())}")
        sys.exit(1)

    # Khởi tạo class downloader
    DownloaderClass = downloaders_map[platform]
    downloader = DownloaderClass(url, option, filename, folder, format_ext)

    # Thực thi tải
    downloader.download()


if __name__ == "__main__":
    main()
