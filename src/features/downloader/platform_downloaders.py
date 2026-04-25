from base_downloader import BaseDownloader

class YoutubeDownloader(BaseDownloader):
    def __init__(self, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None):
        super().__init__("YouTube", url, option, filename, folder, format_ext)

class YoutubeMusicDownloader(BaseDownloader):
    def __init__(self, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None):
        super().__init__("YouTube Music", url, option, filename, folder, format_ext)

class FacebookDownloader(BaseDownloader):
    def __init__(self, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None):
        super().__init__("Facebook", url, option, filename, folder, format_ext)

    def set_good_video_options(self, cmd: list):
        # Thuật toán của FB đôi khi khó phân loại height chính xác bằng thẻ bv* thông thường
        # Dùng fallback an toàn hơn cho FB nếu thẻ height<=720 không có
        cmd.extend(["-f", "bv*[height<=720]+ba/bestvideo[height<=720]+bestaudio/best"])
        self._apply_video_format(cmd)

class InstagramDownloader(BaseDownloader):
    def __init__(self, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None):
        super().__init__("Instagram", url, option, filename, folder, format_ext)

class TiktokDownloader(BaseDownloader):
    def __init__(self, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None):
        super().__init__("TikTok", url, option, filename, folder, format_ext)
        
    def set_good_video_options(self, cmd: list):
        # Tiktok hầu hết không tách luồng riêng, tải 'b' là đủ
        # nhưng vẫn giữ chuẩn chung
        super().set_good_video_options(cmd)
