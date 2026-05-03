import sys
import argparse

# Cho phép import các file cùng cấp
from platform_downloaders import (
    YoutubeDownloader,
    YoutubeMusicDownloader,
    FacebookDownloader,
    InstagramDownloader,
    TiktokDownloader,
    DouyinDownloader,
    BilibiliDownloader,
    SoundCloudDownloader,
    SpotifyDownloader,
)

DEFAULT_DOWNLOAD_OPTION = "good-vid"
DEFAULT_ARIA2_THREADS = 4


def main():
    # Cấu hình UTF-8 cho console Windows để in được tiếng Việt
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Media Studio Downloader Module")
    parser.add_argument(
        "platform",
        type=str,
        help="Nền tảng (ytb, ytb-music, fb, insta, tiktok, douyin, bilibili, bili, bilili, soundcloud, spotify)",
    )
    parser.add_argument("url", type=str, help="URL video cần tải")
    parser.add_argument(
        "option",
        nargs="?",
        default=DEFAULT_DOWNLOAD_OPTION,
        help=f"Tùy chọn tải: best-vid, good-vid, audio, sub (mặc định: {DEFAULT_DOWNLOAD_OPTION})",
    )
    parser.add_argument("--filename", type=str, default=None, help="Tên file đầu ra")
    parser.add_argument("--folder", type=str, default=None, help="Thư mục lưu trữ")
    parser.add_argument("--format", type=str, default=None, help="Định dạng file tải xuống (mp4, mp3, wav...)")
    parser.add_argument("--cookies", type=str, default=None, help="Đường dẫn file cookies Netscape")
    parser.add_argument(
        "--cookies-from-browser",
        type=str,
        default=None,
        help="Lấy cookies từ browser (vd: chrome, edge, firefox)",
    )
    parser.add_argument(
        "--threads",
        "--aria2-threads",
        dest="threads",
        type=int,
        default=DEFAULT_ARIA2_THREADS,
        help=f"Số luồng tải song song cho aria2 (mặc định: {DEFAULT_ARIA2_THREADS})",
    )

    args = parser.parse_args()

    platform = args.platform.lower()
    url = args.url
    option = args.option
    filename = args.filename
    folder = args.folder
    format_ext = args.format
    threads = args.threads
    cookies = args.cookies
    cookies_from_browser = args.cookies_from_browser

    if threads < 1:
        print(">>> Lỗi: --threads phải là số nguyên >= 1.")
        sys.exit(1)
    if cookies and cookies_from_browser:
        print(">>> Lỗi: Chỉ dùng một trong hai flag: --cookies hoặc --cookies-from-browser.")
        sys.exit(1)

    # Map platform code tới các Class tương ứng
    downloaders_map = {
        "ytb": YoutubeDownloader,
        "ytb-music": YoutubeMusicDownloader,
        "fb": FacebookDownloader,
        "insta": InstagramDownloader,
        "tiktok": TiktokDownloader,
        "douyin": DouyinDownloader,
        "bilibili": BilibiliDownloader,
        "bili": BilibiliDownloader,
        "bilili": BilibiliDownloader,
        "soundcloud": SoundCloudDownloader,
        "spotify": SpotifyDownloader,
    }

    if platform not in downloaders_map:
        print(f">>> Lỗi: Nền tảng '{platform}' không được hỗ trợ.")
        print(f"Các nền tảng hợp lệ: {', '.join(downloaders_map.keys())}")
        sys.exit(1)

    # Khởi tạo class downloader
    DownloaderClass = downloaders_map[platform]
    downloader = DownloaderClass(
        url,
        option,
        filename,
        folder,
        format_ext,
        threads,
        cookies,
        cookies_from_browser,
    )

    # Thực thi tải
    downloader.download()


if __name__ == "__main__":
    main()
