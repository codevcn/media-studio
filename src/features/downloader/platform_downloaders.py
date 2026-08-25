import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Đảm bảo src directory nằm trong sys.path để import configs
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from configs.paths import ROOT_FOLDER_PATH
from utils.helpers import clean_url

env_path = os.path.join(ROOT_FOLDER_PATH, ".env")
load_dotenv(dotenv_path=env_path)

from base_downloader import BaseDownloader, DEFAULT_DOWNLOAD_OPTION, ensure_utf8_stdout


class YoutubeDownloader(BaseDownloader):
    def __init__(
        self,
        url: str,
        option: str,
        filename: str | None = None,
        folder: str | None = None,
        format_ext: str | None = None,
        aria2_threads: int = 4,
        slice_time: str | None = None,
    ):
        super().__init__(
            "YouTube",
            url,
            option,
            filename,
            folder,
            format_ext,
            aria2_threads,
            slice_time,
        )

    def build_command(self) -> list[str]:
        cmd = super().build_command()
        if self.slice_time:
            cmd.extend(["--download-sections", f"*{self.slice_time}"])
            print(f">>> [INFO] Cắt video tải xuống từ mốc thời gian: {self.slice_time}")
        return cmd


class YoutubeMusicDownloader(BaseDownloader):
    def __init__(
        self,
        url: str,
        option: str,
        filename: str | None = None,
        folder: str | None = None,
        format_ext: str | None = None,
        aria2_threads: int = 4,
        slice_time: str | None = None,
    ):
        super().__init__(
            "YouTube Music",
            url,
            option,
            filename,
            folder,
            format_ext,
            aria2_threads,
            slice_time,
        )

    def build_command(self) -> list[str]:
        cmd = super().build_command()
        if self.slice_time:
            cmd.extend(["--download-sections", f"*{self.slice_time}"])
            print(f">>> [INFO] Cắt audio tải xuống từ mốc thời gian: {self.slice_time}")
        return cmd


class FacebookDownloader(BaseDownloader):
    def __init__(
        self,
        url: str,
        option: str,
        filename: str | None = None,
        folder: str | None = None,
        format_ext: str | None = None,
        aria2_threads: int = 4,
        slice_time: str | None = None,
    ):
        super().__init__(
            "Facebook",
            url,
            option,
            filename,
            folder,
            format_ext,
            aria2_threads,
            slice_time,
        )

    def set_good_video_options(self, cmd: list):
        # Thuật toán của FB đôi khi khó phân loại height chính xác bằng thẻ bv* thông thường
        # Dùng fallback an toàn hơn cho FB nếu thẻ height<=720 không có
        cmd.extend(["-f", "bv*[height<=720]+ba/bestvideo[height<=720]+bestaudio/best"])
        self._apply_video_format(cmd)


class InstagramDownloader(BaseDownloader):
    def __init__(
        self,
        url: str,
        option: str,
        filename: str | None = None,
        folder: str | None = None,
        format_ext: str | None = None,
        aria2_threads: int = 4,
        slice_time: str | None = None,
    ):
        super().__init__(
            "Instagram",
            url,
            option,
            filename,
            folder,
            format_ext,
            aria2_threads,
            slice_time,
        )


class TiktokDownloader(BaseDownloader):
    """
    Downloader TikTok với cơ chế ưu tiên tải video không watermark.
    Thử format `download_addr-0` (no-watermark) trước.
    Nếu thất bại, tự động fallback sang luồng tải thường (có watermark).
    """

    # Các option video sẽ được thử tải no-watermark trước
    VIDEO_OPTIONS = {"best-video", "best-vid", "good-video", "good-vid"}

    def __init__(
        self,
        url: str,
        option: str,
        filename: str | None = None,
        folder: str | None = None,
        format_ext: str | None = None,
        aria2_threads: int = 4,
        slice_time: str | None = None,
    ):
        super().__init__(
            "TikTok",
            url,
            option,
            filename,
            folder,
            format_ext,
            aria2_threads,
            slice_time,
        )

    def download(self):
        ensure_utf8_stdout()

        # Chỉ thử no-watermark khi tải video, không áp dụng cho audio/sub
        if self.option in self.VIDEO_OPTIONS:
            print(f"[{self.platform_name}] Đang thử tải video không watermark...")
            nw_cmd = self._build_no_watermark_cmd()
            try:
                subprocess.run(nw_cmd, check=True)
                print("-" * 50)
                print(">>> Hoàn tất tải video TikTok không watermark!")
                return
            except subprocess.CalledProcessError:
                print("-" * 50)
                print(
                    ">>> CẢNH BÁO: Không thể tải video không watermark. "
                    "Đang fallback sang phiên bản có watermark..."
                )
                print("-" * 50)
            except FileNotFoundError:
                print(
                    ">>> Lỗi hệ thống: Không tìm thấy 'yt-dlp' hoặc 'aria2c' trên máy tính."
                )
                sys.exit(1)

        # Fallback: tải bình thường qua BaseDownloader (có thể kèm watermark)
        super().download()

    def _build_no_watermark_cmd(self) -> list[str]:
        """Xây dựng lệnh yt-dlp nhắm vào format no-watermark của TikTok."""
        cmd = ["yt-dlp"]

        # Format download_addr-0 là bản không watermark của TikTok
        cmd.extend(["-f", "download_addr-0"])

        # Áp dụng merge format nếu user chỉ định --format
        self._apply_video_format(cmd)

        # Output template
        output_template = "%(title)s.%(ext)s"
        if self.filename:
            output_template = f"{self.filename}.%(ext)s"
        cmd.extend(["-o", output_template])

        # Thư mục đích
        if self.folder:
            cmd.extend(["-P", self.folder])

        # Tăng tốc bằng aria2
        self.apply_aria2_options(cmd)

        # URL
        cmd.append(self.url)

        return cmd





class BilibiliDownloader(BaseDownloader):
    def __init__(
        self,
        url: str,
        option: str,
        filename: str | None = None,
        folder: str | None = None,
        format_ext: str | None = None,
        aria2_threads: int = 4,
        slice_time: str | None = None,
    ):
        super().__init__(
            "Bilibili",
            url,
            option,
            filename,
            folder,
            format_ext,
            aria2_threads,
            slice_time,
        )


class SoundCloudDownloader(BaseDownloader):
    def __init__(
        self,
        url: str,
        option: str,
        filename: str | None = None,
        folder: str | None = None,
        format_ext: str | None = None,
        aria2_threads: int = 4,
        slice_time: str | None = None,
    ):
        super().__init__(
            "SoundCloud",
            url,
            option,
            filename,
            folder,
            format_ext,
            aria2_threads,
            slice_time,
        )

    def set_good_video_options(self, cmd: list):
        # SoundCloud is audio-first; keep good-vid as a practical audio fallback.
        self.set_audio_options(cmd)

    def set_best_video_options(self, cmd: list):
        self.set_audio_options(cmd)


import urllib.request
import urllib.error
import json
import re

class TwitterDownloader(BaseDownloader):
    def __init__(
        self,
        url: str,
        option: str,
        filename: str | None = None,
        folder: str | None = None,
        format_ext: str | None = None,
        aria2_threads: int = 4,
        slice_time: str | None = None,
    ):
        super().__init__(
            "Twitter",
            url,
            option,
            filename,
            folder,
            format_ext,
            aria2_threads,
            slice_time,
        )

    def build_command(self) -> list[str]:
        cmd = super().build_command()
        # Bỏ qua lỗi "Bad guest token" của yt-dlp cho các video/audio thông thường
        cmd.extend(["--extractor-args", "twitter:api=syndication"])
        return cmd

    def download(self):
        if self.option == "img":
            print(f"[{self.platform_name}] Đang dùng vxtwitter API để tải ảnh (tránh lỗi yt-dlp)...")
            self._download_images_via_vxtwitter()
        else:
            super().download()

    def _download_images_via_vxtwitter(self):
        # Trích xuất tweet ID từ URL
        match = re.search(r"status/(\d+)", self.url)
        if not match:
            print(f">>> LỖI: Không tìm thấy ID bài viết trong URL '{self.url}'.")
            sys.exit(1)
        tweet_id = match.group(1)
        
        api_url = f"https://api.vxtwitter.com/i/status/{tweet_id}"
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f">>> LỖI: Không thể kết nối đến vxtwitter API: {e}")
            sys.exit(1)

        media_urls = data.get("mediaURLs", [])
        if not media_urls:
            print(f">>> Không tìm thấy ảnh nào trong bài đăng này.")
            return

        out_dir = Path(self.folder) if self.folder else Path(".")
        out_dir.mkdir(parents=True, exist_ok=True)
        
        for idx, m_url in enumerate(media_urls):
            ext = m_url.split(".")[-1]
            if len(ext) > 4: ext = "jpg" # Fallback
            
            base_name = self.filename if self.filename else tweet_id
            suffix = f"_{idx}" if len(media_urls) > 1 else ""
            out_file = out_dir / f"{base_name}{suffix}.{ext}"
            
            print(f"  Đang tải: {out_file}...")
            try:
                urllib.request.urlretrieve(m_url, str(out_file))
            except Exception as e:
                print(f"  -> Lỗi tải {m_url}: {e}")
        
        print("-" * 50)
        print(">>> Hoàn tất tải ảnh từ Twitter!")


class SpotifyDownloader:
    VALID_AUDIO_OPTIONS = {"audio", "good-vid", "good-video", "best-vid", "best-video"}

    def __init__(
        self,
        url: str,
        option: str,
        filename: str | None = None,
        folder: str | None = None,
        format_ext: str | None = None,
        aria2_threads: int = 4,
        slice_time: str | None = None,
    ):
        self.platform_name = "Spotify"
        self.url = clean_url(url, "spotify")
        self.option = option or DEFAULT_DOWNLOAD_OPTION
        self.filename = filename
        self.folder = folder
        self.format_ext = (format_ext or "mp3").lower()
        self.threads = max(1, int(aria2_threads or 4))

    def download(self):
        ensure_utf8_stdout()

        if self.option == "sub":
            print(
                ">>> Lỗi: Spotify không hỗ trợ tải phụ đề. Vui lòng dùng option audio."
            )
            sys.exit(1)
        if self.option not in self.VALID_AUDIO_OPTIONS:
            print(
                ">>> Lỗi: Option Spotify hợp lệ: audio. Có thể bỏ qua option để dùng mặc định."
            )
            sys.exit(1)

        if self.option != "audio":
            print("[INFO] Spotify là nguồn audio; đang dùng spotDL để tải nhạc.")

        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not client_id or not client_secret:
            print(
                ">>> LỖI: Thiếu thông tin SPOTIFY_CLIENT_ID hoặc SPOTIFY_CLIENT_SECRET trong file .env"
            )
            print(
                "Mặc định spotDL dùng chung Client ID nên rất dễ bị Spotify chặn (lỗi 'rate limit 86400s')."
            )
            print("Để khắc phục, vui lòng:")
            print(
                "1. Truy cập https://developer.spotify.com/dashboard tạo 1 app miễn phí."
            )
            print(
                "2. Copy 'Client ID' và 'Client Secret' dán vào file .env ở thư mục gốc của tool."
            )
            sys.exit(1)

        cmd = self.build_command()
        print(f"[{self.platform_name}] Đang bắt đầu tải audio...")
        print(f"URL: {self.url}")
        print(f"spotDL threads: {self.threads}")

        try:
            subprocess.run(cmd, check=True)
            print("-" * 50)
            print(">>> Hoàn tất tải xuống Spotify thành công!")
        except FileNotFoundError:
            print(">>> Lỗi hệ thống: Không tìm thấy lệnh 'spotdl'.")
            print("Vui lòng cài spotDL như CLI riêng, ví dụ:")
            print("  python -m pip install --user pipx")
            print("  python -m pipx ensurepath")
            print("  python -m pipx install spotdl")
            print(
                "Không nên cài spotDL vào requirements chung vì dependency của spotDL có thể xung đột với package khác."
            )
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print("-" * 50)
            print(
                f">>> LỖI: Quá trình tải bằng spotDL thất bại (Mã lỗi {e.returncode})."
            )
            print("Gợi ý khắc phục:")
            print(
                "  - Kiểm tra URL Spotify track/album/playlist/artist có public và hợp lệ không."
            )
            print(
                "  - SpotDL tải audio bằng nguồn khớp từ YouTube/YouTube Music, nên kết quả phụ thuộc khả năng tìm thấy bản tương ứng."
            )
            print("-" * 50)
            sys.exit(1)

    def build_command(self) -> list[str]:
        cmd = [
            "spotdl",
            "download",
            self.url,
            "--format",
            self.format_ext,
            "--threads",
            str(self.threads),
        ]

        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        if client_id and client_secret:
            cmd.extend(["--client-id", client_id, "--client-secret", client_secret])

        output_template = self._build_output_template()
        if output_template:
            cmd.extend(["--output", output_template])

        return cmd

    def _build_output_template(self) -> str | None:
        output_name = "{artists} - {title}.{output-ext}"
        if self.filename:
            filename_path = Path(self.filename)
            stem = (
                str(filename_path.with_suffix(""))
                if filename_path.suffix
                else self.filename
            )
            output_name = f"{stem}.{{output-ext}}"

        if self.folder:
            return str(Path(self.folder) / output_name)

        return output_name
