from base_downloader import BaseDownloader

class YoutubeDownloader(BaseDownloader):
    def __init__(self, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None, aria2_threads: int = 4, cookies: str | None = None, cookies_from_browser: str | None = None):
        super().__init__("YouTube", url, option, filename, folder, format_ext, aria2_threads, cookies, cookies_from_browser)

class YoutubeMusicDownloader(BaseDownloader):
    def __init__(self, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None, aria2_threads: int = 4, cookies: str | None = None, cookies_from_browser: str | None = None):
        super().__init__("YouTube Music", url, option, filename, folder, format_ext, aria2_threads, cookies, cookies_from_browser)

class FacebookDownloader(BaseDownloader):
    def __init__(self, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None, aria2_threads: int = 4, cookies: str | None = None, cookies_from_browser: str | None = None):
        super().__init__("Facebook", url, option, filename, folder, format_ext, aria2_threads, cookies, cookies_from_browser)

    def set_good_video_options(self, cmd: list):
        # Thuật toán của FB đôi khi khó phân loại height chính xác bằng thẻ bv* thông thường
        # Dùng fallback an toàn hơn cho FB nếu thẻ height<=720 không có
        cmd.extend(["-f", "bv*[height<=720]+ba/bestvideo[height<=720]+bestaudio/best"])
        self._apply_video_format(cmd)

class InstagramDownloader(BaseDownloader):
    def __init__(self, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None, aria2_threads: int = 4, cookies: str | None = None, cookies_from_browser: str | None = None):
        super().__init__("Instagram", url, option, filename, folder, format_ext, aria2_threads, cookies, cookies_from_browser)

class TiktokDownloader(BaseDownloader):
    def __init__(self, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None, aria2_threads: int = 4, cookies: str | None = None, cookies_from_browser: str | None = None):
        super().__init__("TikTok", url, option, filename, folder, format_ext, aria2_threads, cookies, cookies_from_browser)
        
    def set_good_video_options(self, cmd: list):
        # Tiktok hầu hết không tách luồng riêng, tải 'b' là đủ
        # nhưng vẫn giữ chuẩn chung
        super().set_good_video_options(cmd)

class DouyinDownloader(BaseDownloader):
    def __init__(self, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None, aria2_threads: int = 4, cookies: str | None = None, cookies_from_browser: str | None = None):
        cookie_fallbacks = None
        if not cookies and not cookies_from_browser:
            cookie_fallbacks = ["chrome", "edge", "firefox"]

        super().__init__(
            "Douyin",
            url,
            option,
            filename,
            folder,
            format_ext,
            aria2_threads,
            cookies,
            cookies_from_browser,
            cookie_fallbacks,
        )

    def set_good_video_options(self, cmd: list):
        # Douyin thường chỉ có một luồng video/audio đã ghép sẵn; fallback 'best' ổn định hơn.
        cmd.extend(["-f", "b[height<=720]/best"])
        self._apply_video_format(cmd)

class BilibiliDownloader(BaseDownloader):
    def __init__(self, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None, aria2_threads: int = 4, cookies: str | None = None, cookies_from_browser: str | None = None):
        super().__init__("Bilibili", url, option, filename, folder, format_ext, aria2_threads, cookies, cookies_from_browser)
