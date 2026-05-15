import subprocess
import sys

DEFAULT_DOWNLOAD_OPTION = "good-vid"
DEFAULT_ARIA2_THREADS = 4


def ensure_utf8_stdout():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")


class BaseDownloader:
    """
    Lớp cơ sở cung cấp chức năng gọi yt-dlp với cấu hình chung.
    Các nền tảng có thể kế thừa và ghi đè các cấu hình này nếu cần.
    """

    def __init__(
        self,
        platform_name: str,
        url: str,
        option: str,
        filename: str | None = None,
        folder: str | None = None,
        format_ext: str | None = None,
        aria2_threads: int = DEFAULT_ARIA2_THREADS,
        cookies: str | None = None,
        cookies_from_browser: str | None = None,
        cookie_browser_fallbacks: list[str] | None = None,
    ):
        self.platform_name = platform_name
        self.url = url
        self.option = option or DEFAULT_DOWNLOAD_OPTION
        self.filename = filename
        self.folder = folder
        self.format_ext = format_ext
        self.aria2_threads = self._normalize_aria2_threads(aria2_threads)
        self.cookies = cookies
        self.cookies_from_browser = cookies_from_browser
        self.cookie_browser_fallbacks = cookie_browser_fallbacks or []

    def download(self):
        ensure_utf8_stdout()

        commands = self.build_download_commands()

        print(f"[{self.platform_name}] Đang bắt đầu tải ({self.option})...")
        print(f"URL: {self.url}")
        if self.option not in ("sub", "thumb"):
            print(f"aria2 threads: {self.aria2_threads}")
        if len(commands) > 1:
            browsers = ", ".join(browser for browser, _ in commands if browser)
            print(f"cookies-from-browser auto: {browsers}")

        last_error = None
        for browser, cmd in commands:
            if browser:
                print(f"[INFO] Thử cookies từ browser: {browser}")

            try:
                # Chạy yt-dlp và in output trực tiếp ra màn hình để người dùng thấy % tiến độ
                subprocess.run(cmd, check=True)
                print("-" * 50)
                print(">>> Hoàn tất tải xuống thành công!")
                return

            except subprocess.CalledProcessError as e:
                last_error = e
                if browser and browser != commands[-1][0]:
                    print(f">>> Chưa tải được với cookies từ {browser}, thử browser tiếp theo...")
                    continue
                self.handle_error(e)
                sys.exit(1)
            except FileNotFoundError:
                print(">>> Lỗi hệ thống: Không tìm thấy 'yt-dlp' hoặc 'aria2c' trên máy tính.")
                print("Vui lòng cài đặt yt-dlp bằng lệnh: pip install yt-dlp và cài aria2 để có lệnh aria2c.")
                sys.exit(1)
            except Exception as e:
                print(f">>> Lỗi không xác định: {e}")
                sys.exit(1)

        if last_error:
            self.handle_error(last_error)
            sys.exit(1)

    def build_download_commands(self) -> list[tuple[str | None, list[str]]]:
        if self.cookie_browser_fallbacks and not self.cookies and not self.cookies_from_browser:
            return [
                (browser, self.build_command(cookies_from_browser=browser))
                for browser in self.cookie_browser_fallbacks
            ]

        return [(None, self.build_command())]

    def build_command(self, cookies_from_browser: str | None = None) -> list[str]:
        cmd = ["yt-dlp"]

        # 1. Option mapping
        # Auto-detect: nếu --format là audio format nhưng --option là video → chuyển sang audio
        AUDIO_FORMATS = {"mp3", "m4a", "wav", "flac", "opus", "vorbis", "aac", "alac"}
        VIDEO_OPTIONS = {"best-video", "best-vid", "good-video", "good-vid"}
        effective_option = self.option
        if (
            self.format_ext
            and self.format_ext.lower() in AUDIO_FORMATS
            and effective_option in VIDEO_OPTIONS
        ):
            print(
                f">>> [INFO] --format '{self.format_ext}' là audio format. "
                f"Tự động chuyển --option từ '{effective_option}' sang 'audio'."
            )
            effective_option = "audio"

        if effective_option in ("best-video", "best-vid"):
            self.set_best_video_options(cmd)
        elif effective_option in ("good-video", "good-vid"):
            self.set_good_video_options(cmd)
        elif effective_option == "audio":
            self.set_audio_options(cmd)
        elif effective_option == "sub":
            self.set_sub_options(cmd)
        elif effective_option == "thumb":
            self.set_thumb_options(cmd)
        elif effective_option == "img":
            self.set_img_options(cmd)
        else:
            print(
                f">>> Lỗi: Option '{self.option}' không hợp lệ. Vui lòng chọn: best-vid, good-vid, audio, sub, thumb, img."
            )
            sys.exit(1)

        # 2. Định dạng filename đầu ra
        output_template = "%(title)s.%(ext)s"
        if self.filename:
            output_template = f"{self.filename}.%(ext)s"
        cmd.extend(["-o", output_template])

        # 3. Thư mục đích
        if self.folder:
            cmd.extend(["-P", self.folder])

        # 4. Cookie giúp các nền tảng như Douyin vượt qua bước xác minh web.
        self.apply_cookie_options(cmd, cookies_from_browser)

        # 5. Tăng tốc tải bằng aria2 cho các nội dung media.
        if self.option not in ("sub", "thumb"):
            self.apply_aria2_options(cmd)

        # 6. Truyền URL
        cmd.append(self.url)

        return cmd

    def set_best_video_options(self, cmd: list):
        """Tải video chất lượng cao nhất."""
        cmd.extend(["-f", "bv*+ba/b"])
        self._apply_video_format(cmd)

    def set_good_video_options(self, cmd: list):
        """Tải video chất lượng khá (thường là 720p)."""
        cmd.extend(["-f", "bv*[height<=720]+ba/b[height<=720] / wv*+ba/w"])
        self._apply_video_format(cmd)

    def _apply_video_format(self, cmd: list):
        if self.format_ext:
            valid_video = ["mkv", "mp4", "ogg", "webm", "flv"]
            if self.format_ext.lower() not in valid_video:
                print(f">>> CẢNH BÁO: Không thể chỉ định định dạng video thành '{self.format_ext}'. yt-dlp chỉ hỗ trợ merge sang: {', '.join(valid_video)}")
                print(">>> Đang chuyển về định dạng gốc mặc định của file.")
            else:
                cmd.extend(["--merge-output-format", self.format_ext.lower()])

    def _normalize_aria2_threads(self, threads: int) -> int:
        try:
            normalized_threads = int(threads)
        except (TypeError, ValueError):
            normalized_threads = DEFAULT_ARIA2_THREADS

        return max(1, normalized_threads)

    def apply_aria2_options(self, cmd: list):
        cmd.extend(
            [
                "--external-downloader",
                "aria2c",
                "--external-downloader-args",
                f"aria2c:-x {self.aria2_threads} -s {self.aria2_threads} -k 1M",
            ]
        )

    def apply_cookie_options(self, cmd: list, cookies_from_browser: str | None = None):
        if self.cookies:
            cmd.extend(["--cookies", self.cookies])
        browser = cookies_from_browser or self.cookies_from_browser
        if browser:
            cmd.extend(["--cookies-from-browser", browser])

    def set_audio_options(self, cmd: list):
        """Tải và chuyển đổi sang dạng audio (mp3)."""
        audio_fmt = self.format_ext.lower() if self.format_ext else "mp3"
        valid_audio = ["best", "aac", "flac", "mp3", "m4a", "opus", "vorbis", "wav", "alac"]
        if audio_fmt not in valid_audio:
            print(f">>> CẢNH BÁO: Định dạng âm thanh '{audio_fmt}' không phổ biến hoặc không được hỗ trợ chính thức.")
            print(f">>> yt-dlp có thể báo lỗi. Hỗ trợ tốt nhất: {', '.join(valid_audio)}")
        cmd.extend(["-x", "--audio-format", audio_fmt])

    def set_sub_options(self, cmd: list):
        """Chỉ tải phụ đề dạng SRT."""
        sub_fmt = self.format_ext.lower() if self.format_ext else "srt"
        valid_sub = ["srt", "vtt", "ass", "lrc"]
        if sub_fmt not in valid_sub:
             print(f">>> CẢNH BÁO: yt-dlp có thể không tải được định dạng phụ đề '{sub_fmt}'. Thường dùng nhất: srt, vtt.")
        cmd.extend(["--write-subs", "--write-auto-subs", "--sub-format", sub_fmt, "--skip-download"])

    def set_thumb_options(self, cmd: list):
        """Chỉ tải ảnh bìa (thumbnail)."""
        cmd.extend(["--write-thumbnail", "--skip-download"])
        if self.format_ext:
            valid_thumb = ["jpg", "png", "webp"]
            if self.format_ext.lower() in valid_thumb:
                cmd.extend(["--convert-thumbnails", self.format_ext.lower()])
            else:
                print(f">>> CẢNH BÁO: yt-dlp có thể không hỗ trợ định dạng ảnh bìa '{self.format_ext}'. Dùng mặc định: jpg/png/webp.")

    def set_img_options(self, cmd: list):
        """Tải toàn bộ ảnh có trong link."""
        cmd.extend(["--write-all-thumbnails"])
        cmd.extend(["-f", "bestimage/best[ext=jpg]/best[ext=png]/best[ext=webp]/bestvideo/best"])

    def handle_error(self, e: subprocess.CalledProcessError):
        """Xử lý ngoại lệ, in ra thông báo dễ hiểu cho người dùng."""
        print("-" * 50)
        print(f">>> LỖI: Quá trình tải bằng yt-dlp thất bại (Mã lỗi {e.returncode}).")
        if self.platform_name.lower() == "douyin":
            print("Ghi chu rieng cho Douyin:")
            print("  - Neu log bao 'Fresh cookies are needed' du da truyen --cookies, day thuong la loi extractor/anti-bot cua Douyin trong yt-dlp, khong chac la file cookie sai.")
            print("  - Hay mo dung link video trong browser, refresh den khi xem duoc, export cookies lai ngay sau do, roi chay lai lenh.")
            print("  - Neu van loi, thu cap nhat yt-dlp len nightly/master vi stable co the chua bat kip thay doi cua Douyin.")
        print("Gợi ý khắc phục:")
        print("  - Xác minh xem URL có trỏ đến nội dung hợp lệ không.")
        print(
            "  - Video có thể bị giới hạn độ tuổi, riêng tư (private) hoặc yêu cầu đăng nhập."
        )
        print("  - Có thể URL không chứa phụ đề nếu bạn chọn option 'sub'.")
        print("  - Với lỗi 'Fresh cookies are needed', hãy thử thêm --cookies-from-browser chrome hoặc --cookies-from-browser edge.")
        print("  - Nếu dùng file cookies, truyền --cookies \"D:\\path\\cookies.txt\".")
        print("  - Nếu lỗi liên quan aria2, hãy kiểm tra lệnh aria2c đã có trong PATH.")
        print(
            "  - Cấu trúc trang web đã thay đổi, hãy thử cập nhật yt-dlp: pip install -U yt-dlp"
        )
        print("-" * 50)
