import subprocess
import sys


class BaseDownloader:
    """
    Lớp cơ sở cung cấp chức năng gọi yt-dlp với cấu hình chung.
    Các nền tảng có thể kế thừa và ghi đè các cấu hình này nếu cần.
    """

    def __init__(self, platform_name: str, url: str, option: str, filename: str | None = None, folder: str | None = None, format_ext: str | None = None):
        self.platform_name = platform_name
        self.url = url
        self.option = option
        self.filename = filename
        self.folder = folder
        self.format_ext = format_ext

    def download(self):
        cmd = ["yt-dlp"]

        # 1. Option mapping
        if self.option in ("best-video", "best-vid"):
            self.set_best_video_options(cmd)
        elif self.option in ("good-video", "good-vid"):
            self.set_good_video_options(cmd)
        elif self.option == "audio":
            self.set_audio_options(cmd)
        elif self.option == "sub":
            self.set_sub_options(cmd)
        else:
            print(
                f">>> Lỗi: Option '{self.option}' không hợp lệ. Vui lòng chọn: best-vid, good-vid, audio, sub."
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

        # 4. Truyền URL
        cmd.append(self.url)

        print(f"[{self.platform_name}] Đang bắt đầu tải ({self.option})...")
        print(f"URL: {self.url}")

        try:
            # Chạy yt-dlp và in output trực tiếp ra màn hình để người dùng thấy % tiến độ
            subprocess.run(cmd, check=True)
            print("-" * 50)
            print(">>> Hoàn tất tải xuống thành công!")

        except subprocess.CalledProcessError as e:
            self.handle_error(e)
            sys.exit(1)
        except FileNotFoundError:
            print(">>> Lỗi hệ thống: Không tìm thấy 'yt-dlp' trên máy tính.")
            print("Vui lòng cài đặt yt-dlp bằng lệnh: pip install yt-dlp")
            sys.exit(1)
        except Exception as e:
            print(f">>> Lỗi không xác định: {e}")
            sys.exit(1)

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

    def handle_error(self, e: subprocess.CalledProcessError):
        """Xử lý ngoại lệ, in ra thông báo dễ hiểu cho người dùng."""
        print("-" * 50)
        print(f">>> LỖI: Quá trình tải bằng yt-dlp thất bại (Mã lỗi {e.returncode}).")
        print("Gợi ý khắc phục:")
        print("  - Xác minh xem URL có trỏ đến nội dung hợp lệ không.")
        print(
            "  - Video có thể bị giới hạn độ tuổi, riêng tư (private) hoặc yêu cầu đăng nhập."
        )
        print("  - Có thể URL không chứa phụ đề nếu bạn chọn option 'sub'.")
        print(
            "  - Cấu trúc trang web đã thay đổi, hãy thử cập nhật yt-dlp: pip install -U yt-dlp"
        )
        print("-" * 50)
