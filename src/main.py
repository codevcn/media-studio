import os
import sys
import subprocess
import argparse

from configs.paths import ROOT_FOLDER_PATH, CONTENTS_FOLDER_PATH

# --- Constants ---
# Types
MDIA_TYPE_AUDIO = "audio"
MDIA_TYPE_VIDEO = "video"
MDIA_TYPE_IMAGE = "image"
MDIA_TYPE_MEDIA = "media"
MDIA_TYPE_APP = "app"
MDIA_TYPE_OPEN = "open"
MDIA_TYPE_GIT = "git"
MDIA_TYPE_DLD = "dld"

# Actions
MDIA_APP_ACTION_VIDEO_PLAYER = "player"
MDIA_VIDEO_ACTION_RM_LOGO = "rm-logo"
MDIA_VIDEO_ACTION_FRAMES = "frames"
MDIA_AUDIO_ACTION_EXTRACT = "extract"
MDIA_MEDIA_ACTION_PART_BY_SIZE = "part-size"
MDIA_MEDIA_ACTION_PART_BY_TIME = "part-time"
MDIA_MEDIA_ACTION_SLICE = "slice"
MDIA_IMAGE_ACTION_FLIP = "flip"
MDIA_IMAGE_FLIP_HORIZONTAL = "horizontal"
MDIA_IMAGE_FLIP_VERTICAL = "vertical"
MDIA_GIT_ACTION_COMMIT = "commit"

# Downloader actions
MDIA_DLD_ACTION_YTB = "ytb"
MDIA_DLD_ACTION_YTB_MUSIC = "ytb-music"
MDIA_DLD_ACTION_FB = "fb"
MDIA_DLD_ACTION_INSTA = "insta"
MDIA_DLD_ACTION_TIKTOK = "tiktok"
MDIA_DLD_ACTION_DOUYIN = "douyin"
MDIA_DLD_ACTION_BILIBILI = "bilibili"
MDIA_DLD_ACTION_BILI = "bili"
MDIA_DLD_ACTION_BILILI = "bilili"
MDIA_DLD_ACTION_SOUNDCLOUD = "scloud"
MDIA_DLD_ACTION_SPOTIFY = "spot"
MDIA_DLD_ACTION_LIST = "list"
MDIA_DLD_DEFAULT_OPTION = "good-vid"
MDIA_DLD_DEFAULT_THREADS = 4

# Warnings
MDIA_WARNING_TYPE_WRONG = "WRONG-TYPE"
MDIA_WARNING_TYPE_MISSING = "MISSING-TYPE"
MDIA_WARNING_ACTION_WRONG = "WRONG-ACTION"
MDIA_WARNING_ACTION_MISSING = "MISSING-ACTION"
MDIA_WARNING_FLAG_MISSING = "MISSING-FLAG"


# --- Helper Functions ---
def get_script_path(relative_path: str) -> str:
    """Trả về absolute path của script con dựa theo file hiện tại"""
    return os.path.join(ROOT_FOLDER_PATH, "src", relative_path)


def get_content_path(filename: str) -> str:
    return os.path.join(CONTENTS_FOLDER_PATH, filename)


def warn_user_error(warning_message: str):
    """In cảnh báo lỗi và kết thúc chương trình"""
    print(f">>> Warn: {warning_message}")


def ensure_utf8_stdout():
    """Cấu hình stdout UTF-8 để in tiếng Việt ổn định trên Windows."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")


# --- Handlers ---
def run_app_video_player():
    script_path = get_script_path("apps/video_player/video_player.py")
    subprocess.run([sys.executable, script_path])
    sys.exit(0)


def run_video_rm_logo(input_path: str, coords: str, output_path=None):
    if not input_path or not coords:
        raise Exception(
            f"{MDIA_WARNING_ACTION_MISSING} - Cần truyền ít nhất 2 tham số: input_path và tọa độ x,y,w,h"
        )

    script_path = get_script_path("features/video/video_watermark_remover.py")
    cmd = [sys.executable, script_path, input_path, coords]
    if output_path:
        cmd.append(output_path)
    subprocess.run(cmd)
    sys.exit(0)


def run_video_frames(input_path: str, gap_time: str, limit=None):
    if not input_path or not gap_time:
        raise Exception(
            f"{MDIA_WARNING_ACTION_MISSING} - Cần truyền ít nhất 2 tham số: input_path và gap_time"
        )

    script_path = get_script_path("features/video/extract_frames.py")
    cmd = [sys.executable, script_path, input_path, gap_time]
    if limit:
        cmd.append(limit)
    subprocess.run(cmd)
    sys.exit(0)


def run_audio_extract(input_path: str, output_path: str):
    if not input_path or not output_path:
        raise Exception(
            f"{MDIA_WARNING_ACTION_MISSING} - Cần truyền vào 2 tham số: input_path và output_path"
        )

    script_path = get_script_path("features/audio/extract_audio.py")
    subprocess.run([sys.executable, script_path, input_path, output_path])
    sys.exit(0)


def run_media_part_by_size(input_path: str, size_mb: str, limit=None):
    if not input_path or not size_mb:
        raise Exception(
            f"{MDIA_WARNING_ACTION_MISSING} - Cần truyền vào ít nhất 2 tham số: input_path và size_mb"
        )

    script_path = get_script_path("features/media/part_media_by_size.py")
    cmd = [sys.executable, script_path, input_path, size_mb]
    if limit:
        cmd.append(limit)
    subprocess.run(cmd)
    sys.exit(0)


def run_media_slice(input_path: str, time_range: str, output_filename=None):
    if not input_path or not time_range:
        raise Exception(
            f"{MDIA_WARNING_ACTION_MISSING} - Cần truyền ít nhất 2 tham số: input_path và time_range (vd: 00:10-01:22)"
        )

    script_path = get_script_path("features/media/slice_media.py")
    cmd = [sys.executable, script_path, input_path, time_range]
    if output_filename:
        cmd.append(output_filename)
    subprocess.run(cmd)
    sys.exit(0)


def run_media_part_by_time(input_path: str, duration: str, limit=None):
    if not input_path or not duration:
        raise Exception(
            f"{MDIA_WARNING_ACTION_MISSING} - Cần truyền vào ít nhất 2 tham số: input_path và duration (ví dụ: 20s, 3p)"
        )

    script_path = get_script_path("features/media/part_media_by_time.py")
    cmd = [sys.executable, script_path, input_path, duration]
    if limit:
        cmd.append(limit)
    subprocess.run(cmd)
    sys.exit(0)


def run_image_flip(input_path: str, direction: str, output_path=None):
    if not input_path or not direction:
        raise Exception(
            f"{MDIA_WARNING_ACTION_MISSING} - Cần truyền input_path absolute và hướng lật ({MDIA_IMAGE_FLIP_HORIZONTAL} hoặc {MDIA_IMAGE_FLIP_VERTICAL})"
        )

    script_path = get_script_path("features/image/flip_image.py")
    cmd = [sys.executable, script_path, input_path, direction]
    if output_path:
        cmd.append(output_path)
    subprocess.run(cmd)
    sys.exit(0)


def run_downloader(
    platform: str,
    url: str,
    option: str,
    filename: str,
    folder: str,
    format_ext: str,
    threads: int,
    cookies: str,
    cookies_from_browser: str,
):
    if not url:
        raise Exception(
            f"{MDIA_WARNING_ACTION_MISSING} - Cần truyền URL. Option mặc định là {MDIA_DLD_DEFAULT_OPTION}."
        )

    option = option or MDIA_DLD_DEFAULT_OPTION
    if threads < 1:
        raise Exception("--threads phải là số nguyên >= 1")
    if cookies and cookies_from_browser:
        raise Exception(
            "Chỉ dùng một trong hai flag: --cookies hoặc --cookies-from-browser"
        )

    script_path = get_script_path("features/downloader/run_downloader.py")
    cmd = [sys.executable, script_path, platform, url, "--option", option]
    if filename:
        cmd.extend(["--filename", filename])
    if folder:
        cmd.extend(["--folder", folder])
    if format_ext:
        cmd.extend(["--format", format_ext])
    cmd.extend(["--threads", str(threads)])
    if cookies:
        cmd.extend(["--cookies", cookies])
    if cookies_from_browser:
        cmd.extend(["--cookies-from-browser", cookies_from_browser])

    subprocess.run(cmd)
    sys.exit(0)


def run_douyin_advanced(
    url: str, folder: str | None = None, mode: str | None = None, threads: int = 5
):
    if not url:
        raise Exception(f"{MDIA_WARNING_ACTION_MISSING} - Cần truyền URL Douyin.")

    script_path = get_script_path("features/downloader/douyin_downloader.py")
    cmd = [sys.executable, script_path, url]
    if folder:
        cmd.extend(["--folder", folder])
    if mode:
        cmd.extend(["--mode", mode])
    if threads:
        cmd.extend(["--threads", str(threads)])

    subprocess.run(cmd)
    sys.exit(0)


# --- Khối Dispatcher (__main__) ---
def print_help():
    help_path = get_content_path("help.txt")
    if os.path.exists(help_path):
        with open(help_path, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("Không tìm thấy file help.txt")


def open_this_project_in_IDE(args):
    ide_prefix = "anti" if args.anti else "code"
    command_str = f'{ide_prefix} "{ROOT_FOLDER_PATH}"'
    subprocess.run(command_str, shell=True)
    sys.exit(0)


def open_this_project_in_system_folder():
    folder_path = (
        ROOT_FOLDER_PATH
        if ROOT_FOLDER_PATH
        else os.path.dirname(os.path.abspath(__file__))
    )

    # Sử dụng os.startfile (cách chuẩn nhất trên Windows để mở thư mục/file bằng app mặc định)
    if hasattr(os, "startfile"):
        os.startfile(folder_path)
    else:
        # Dự phòng gọi thẳng explorer
        subprocess.run(["explorer", os.path.normpath(folder_path)])

    sys.exit(0)


def run_git_commit_and_push(message: str):
    if not message:
        raise Exception(
            f"{MDIA_WARNING_FLAG_MISSING} - Lệnh git commit yêu cầu cờ -m 'thông điệp'"
        )

    script_path = get_script_path("features/system/_media_studio_git.py")
    subprocess.run([sys.executable, script_path, "commit", message])
    sys.exit(0)


def main():
    ensure_utf8_stdout()

    if len(sys.argv) == 1 or "-h" in sys.argv or "--help" in sys.argv:
        print_help()
        sys.exit(0)

    parser = argparse.ArgumentParser(
        description="Media Studio CLI Runner", add_help=False
    )
    # Các tham số theo pattern của runner.py
    parser.add_argument(
        "type",
        nargs="?",
        help="Loại lệnh: app | audio | video | image | media | open | git | dld",
    )
    parser.add_argument(
        "action",
        nargs="?",
        help="Hành động (ví dụ: vid-player, rm-logo, extract, slice, flip, commit) hoặc nền tảng download",
    )
    parser.add_argument("value", nargs="?", help="Giá trị thứ nhất")
    parser.add_argument("extra", nargs="?", help="Giá trị thứ hai")
    parser.add_argument("limit", nargs="?", help="Giới hạn số lượng (optional)")
    parser.add_argument(
        "-a", "--anti", action="store_true", help="Dùng Antigravity IDE thay vì VSCode"
    )
    parser.add_argument(
        "-f",
        "--file_explorer",
        action="store_true",
        help="Mở thư mục dự án trong File Explorer",
    )
    parser.add_argument(
        "--des", action="store_true", help="Hiện mô tả chi tiết của lệnh"
    )
    parser.add_argument(
        "-m",
        "--message",
        type=str,
        help="Truyền message cho script phụ (dùng cho git commit)",
    )
    parser.add_argument(
        "--filename", type=str, help="Chỉ định tên file (dùng cho module dld)"
    )
    parser.add_argument(
        "--folder", type=str, help="Chỉ định thư mục đích (dùng cho module dld)"
    )
    parser.add_argument(
        "--format", type=str, help="Chỉ định định dạng đầu ra (dùng cho module dld)"
    )
    parser.add_argument(
        "--option",
        type=str,
        default=MDIA_DLD_DEFAULT_OPTION,
        help=f"Tùy chọn chất lượng tải cho yt-dlp: best-vid, good-vid, audio, sub, thumb (mặc định: {MDIA_DLD_DEFAULT_OPTION})",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["post", "like", "mix", "music", "favorites"],
        default=None,
        help="Chế độ batch cho Douyin: post | like | mix | music | favorites",
    )
    parser.add_argument(
        "--threads",
        "--aria2-threads",
        dest="threads",
        type=int,
        default=MDIA_DLD_DEFAULT_THREADS,
        help=f"Số luồng tải song song cho aria2 (dùng cho module dld, mặc định {MDIA_DLD_DEFAULT_THREADS})",
    )
    parser.add_argument(
        "--cookies",
        type=str,
        help="Đường dẫn file cookies Netscape dùng cho module dld",
    )
    parser.add_argument(
        "--cookies-from-browser",
        type=str,
        help="Lấy cookies từ browser cho module dld (vd: chrome, edge, firefox)",
    )

    args = parser.parse_args()

    cmd_type = args.type
    cmd_action = args.action
    cmd_value = args.value
    cmd_extra = args.extra
    cmd_limit = args.limit

    if args.des:
        if not cmd_type:
            print(
                ">>> Warn: Vui lòng nhập <type> (vd: app, video...) cùng với `--des` để đọc mô tả lệnh."
            )
            sys.exit(1)

        script_path = get_script_path("features/system/_print_feature_description.py")
        run_cmd = [sys.executable, script_path, "--type", cmd_type]
        if cmd_action:
            run_cmd.extend(["--action", cmd_action])

        subprocess.run(run_cmd)
        sys.exit(0)

    try:
        # Bước kiểm tra type
        if cmd_type is None:
            raise Exception(MDIA_WARNING_TYPE_MISSING)

        # -------------------------------------------------------------
        # Dispatcher cho nhóm APP
        # -------------------------------------------------------------
        if cmd_type == MDIA_TYPE_APP:
            if cmd_action == MDIA_APP_ACTION_VIDEO_PLAYER:
                run_app_video_player()
            elif cmd_action is None:
                raise Exception(MDIA_WARNING_ACTION_MISSING)
            else:
                raise Exception(MDIA_WARNING_ACTION_WRONG)

        # -------------------------------------------------------------
        # Dispatcher cho nhóm VIDEO
        # -------------------------------------------------------------
        elif cmd_type == MDIA_TYPE_VIDEO:
            if cmd_action == MDIA_VIDEO_ACTION_RM_LOGO:
                run_video_rm_logo(cmd_value, cmd_extra, cmd_limit)
            elif cmd_action == MDIA_VIDEO_ACTION_FRAMES:
                run_video_frames(cmd_value, cmd_extra, cmd_limit)
            elif cmd_action is None:
                raise Exception(MDIA_WARNING_ACTION_MISSING)
            else:
                raise Exception(MDIA_WARNING_ACTION_WRONG)

        # -------------------------------------------------------------
        # Dispatcher cho nhóm AUDIO
        # -------------------------------------------------------------
        elif cmd_type == MDIA_TYPE_AUDIO:
            if cmd_action == MDIA_AUDIO_ACTION_EXTRACT:
                run_audio_extract(cmd_value, cmd_extra)
            elif cmd_action is None:
                raise Exception(MDIA_WARNING_ACTION_MISSING)
            else:
                raise Exception(MDIA_WARNING_ACTION_WRONG)

        # -------------------------------------------------------------
        # Dispatcher cho nhóm MEDIA
        # -------------------------------------------------------------
        elif cmd_type == MDIA_TYPE_MEDIA:
            if cmd_action == MDIA_MEDIA_ACTION_SLICE:
                run_media_slice(cmd_value, cmd_extra, cmd_limit)
            elif cmd_action == MDIA_MEDIA_ACTION_PART_BY_SIZE:
                run_media_part_by_size(cmd_value, cmd_extra, cmd_limit)
            elif cmd_action == MDIA_MEDIA_ACTION_PART_BY_TIME:
                run_media_part_by_time(cmd_value, cmd_extra, cmd_limit)
            elif cmd_action is None:
                raise Exception(MDIA_WARNING_ACTION_MISSING)
            else:
                raise Exception(MDIA_WARNING_ACTION_WRONG)

        # -------------------------------------------------------------
        # Dispatcher cho nhóm OPEN
        # -------------------------------------------------------------
        elif cmd_type == MDIA_TYPE_OPEN:
            if args.file_explorer:
                open_this_project_in_system_folder()
            else:
                open_this_project_in_IDE(args)

        # -------------------------------------------------------------
        # Dispatcher cho nhóm GIT
        # -------------------------------------------------------------
        elif cmd_type == MDIA_TYPE_GIT:
            if cmd_action == MDIA_GIT_ACTION_COMMIT:
                run_git_commit_and_push(args.message)
            elif cmd_action is None:
                raise Exception(MDIA_WARNING_ACTION_MISSING)
            else:
                raise Exception(MDIA_WARNING_ACTION_WRONG)

        # -------------------------------------------------------------
        # Dispatcher cho nhóm IMAGE
        # -------------------------------------------------------------
        elif cmd_type == MDIA_TYPE_IMAGE:
            if cmd_action == MDIA_IMAGE_ACTION_FLIP:
                run_image_flip(cmd_value, cmd_extra, cmd_limit)
            elif cmd_action is None:
                raise Exception(MDIA_WARNING_ACTION_MISSING)
            else:
                raise Exception(MDIA_WARNING_ACTION_WRONG)

        # -------------------------------------------------------------
        # Dispatcher cho nhóm DLD (Downloader)
        # -------------------------------------------------------------
        elif cmd_type == MDIA_TYPE_DLD:
            valid_actions = [
                MDIA_DLD_ACTION_YTB,
                MDIA_DLD_ACTION_YTB_MUSIC,
                MDIA_DLD_ACTION_FB,
                MDIA_DLD_ACTION_INSTA,
                MDIA_DLD_ACTION_TIKTOK,
                MDIA_DLD_ACTION_BILIBILI,
                MDIA_DLD_ACTION_BILI,
                MDIA_DLD_ACTION_BILILI,
                MDIA_DLD_ACTION_SOUNDCLOUD,
                MDIA_DLD_ACTION_SPOTIFY,
            ]
            if cmd_action == MDIA_DLD_ACTION_LIST:
                print("Các nền tảng được hỗ trợ cho lệnh 'dld':")
                print("  - ytb       : YouTube")
                print("  - ytb-music : YouTube Music")
                print("  - fb        : Facebook")
                print("  - insta     : Instagram")
                print("  - tiktok    : TikTok")
                print("  - douyin    : Douyin")
                print("  - bilibili  : Bilibili (alias: bili, bilili)")
                print("  - soundcloud: SoundCloud (alias: scloud)")
                print("  - spotify   : Spotify (alias: spot)")
                sys.exit(0)
            elif cmd_action == MDIA_DLD_ACTION_DOUYIN:
                run_douyin_advanced(cmd_value, args.folder, args.mode, args.threads)
            elif cmd_action in valid_actions:
                run_downloader(
                    cmd_action,
                    cmd_value,
                    args.option,
                    args.filename,
                    args.folder,
                    args.format,
                    args.threads,
                    args.cookies,
                    args.cookies_from_browser,
                )
            elif cmd_action is None:
                raise Exception(MDIA_WARNING_ACTION_MISSING)
            else:
                raise Exception(MDIA_WARNING_ACTION_WRONG)

        # Type tồn tại nhưng không thuộc các hằng số phía trên
        else:
            raise Exception(MDIA_WARNING_TYPE_WRONG)

    except KeyboardInterrupt:
        print(">>> Tiến trình đã bị hủy bởi người dùng (KeyboardInterrupt).")
        sys.exit(0)
    except Exception as e:
        warn_user_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
