import sys
import argparse
import os

# Ensure src directory is in sys.path
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Cho phép import các file cùng cấp
from platform_downloaders import (
    YoutubeDownloader,
    YoutubeMusicDownloader,
    FacebookDownloader,
    InstagramDownloader,
    TiktokDownloader,
    BilibiliDownloader,
    SoundCloudDownloader,
    SpotifyDownloader,
    TwitterDownloader,
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
        help="Nền tảng (ytb, ytb-music, fb, insta, tiktok, douyin, bilibili, bili, bilili, soundcloud, spotify, twitter, x)",
    )
    parser.add_argument("url", type=str, help="URL video cần tải")
    parser.add_argument(
        "--option",
        type=str,
        default=DEFAULT_DOWNLOAD_OPTION,
        help=f"Tùy chọn tải: best-vid, good-vid, audio, sub, thumb, img (mặc định: {DEFAULT_DOWNLOAD_OPTION})",
    )
    parser.add_argument("--filename", type=str, default=None, help="Tên file đầu ra")
    parser.add_argument("--folder", type=str, default=None, help="Thư mục lưu trữ")
    parser.add_argument(
        "--format",
        type=str,
        default=None,
        help="Định dạng file tải xuống (mp4, mp3, wav...)",
    )
    parser.add_argument(
        "--slice",
        type=str,
        default=None,
        help="Cắt khoảng thời gian khi tải (chỉ Youtube). Vd: 00:10-01:22",
    )
    parser.add_argument("--noti", type=str, default=None, help="Gửi thông báo")

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
    slice_time = args.slice
    noti = args.noti

    if threads < 1:
        print(">>> Lỗi: --threads phải là số nguyên >= 1.")
        sys.exit(1)

    # Map platform code tới các Class tương ứng
    downloaders_map = {
        "ytb": YoutubeDownloader,
        "ytb-music": YoutubeMusicDownloader,
        "fb": FacebookDownloader,
        "insta": InstagramDownloader,
        "tiktok": TiktokDownloader,
        "bilibili": BilibiliDownloader,
        "bili": BilibiliDownloader,
        "bilili": BilibiliDownloader,
        "soundcloud": SoundCloudDownloader,
        "scloud": SoundCloudDownloader,
        "spot": SpotifyDownloader,
        "twitter": TwitterDownloader,
        "x": TwitterDownloader,
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
        slice_time,
    )

    # Thực thi tải
    try:
        downloader.download()
        if noti:
            from utils.notifiers import NotifierFactory

            notifier = NotifierFactory.get_notifier(noti)
            if notifier:
                notifier.notify(f'✅ "mda dld" đã tải xong từ nền tảng {platform}:\n{url}')
    except Exception as e:
        if noti:
            from utils.notifiers import NotifierFactory

            notifier = NotifierFactory.get_notifier(noti)
            if notifier:
                notifier.notify(
                    f"❌ Lỗi tải nền tảng {platform}:\n{url}\n\nChi tiết: {str(e)}"
                )
        raise e


if __name__ == "__main__":
    main()
