import sys
import subprocess
import os


def ensure_utf8_stdout():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")


def get_ytdlp_version() -> str | None:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "yt-dlp"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None


def update_ytdlp():
    ensure_utf8_stdout()

    print("=" * 60)
    print(">>> MEDIA STUDIO — CẬP NHẬT YT-DLP")
    print("=" * 60)

    current_ver = get_ytdlp_version()
    if current_ver:
        print(f"[*] Phiên bản hiện tại: {current_ver}")
    else:
        print("[*] Chưa phát hiện phiên bản yt-dlp hiện tại hoặc chưa cài đặt.")

    print("\n[*] Đang kiểm tra và tải phiên bản mới nhất từ PyPI...")
    print(f"[*] Lệnh thực thi: {sys.executable} -m pip install -U yt-dlp\n")

    cmd = [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"]

    try:
        subprocess.run(cmd, check=True)
        new_ver = get_ytdlp_version()
        print("\n" + "-" * 60)
        if current_ver and new_ver and current_ver == new_ver:
            print(f">>> [OK] yt-dlp đã ở phiên bản mới nhất ({new_ver})!")
        else:
            print(
                f">>> [THÀNH CÔNG] Đã nâng cấp yt-dlp lên phiên bản: {new_ver or 'mới nhất'}!"
            )
        print("=" * 60)
    except subprocess.CalledProcessError as e:
        print("\n" + "-" * 60)
        print(f">>> [LỖI] Cập nhật yt-dlp thất bại (Mã lỗi: {e.returncode}).")
        print("Gợi ý khắc phục:")
        print("  - Kiểm tra kết nối mạng Internet.")
        print("  - Thử chạy lại terminal với quyền Administrator nếu gặp lỗi Permission.")
        print(f"  - Thử chạy thủ công: {sys.executable} -m pip install -U yt-dlp")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print(f">>> [LỖI KHÔNG XÁC ĐỊNH]: {e}")
        sys.exit(1)


if __name__ == "__main__":
    update_ytdlp()
