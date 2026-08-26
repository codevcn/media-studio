import os
import sys
import shlex
import subprocess


def ensure_utf8_stdout():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")


ensure_utf8_stdout()

from colorama import init

init(autoreset=True)

# ---------------------------------------------------------------------------
# Bảng ánh xạ Type & Action (luôn sắp xếp A-Z) và mô tả tóm tắt
# ---------------------------------------------------------------------------
TYPE_ACTION_MAP = {
    "app": ["player"],
    "audio": ["extract"],
    "dld": [
        "bili",
        "bilibili",
        "bilili",
        "douyin",
        "fb",
        "insta",
        "list",
        "scloud",
        "soundcloud",
        "spot",
        "spotify",
        "tiktok",
        "twitter",
        "update",
        "x",
        "ytb",
        "ytb-music",
    ],
    "git": ["commit"],
    "image": ["flip", "rotate"],
    "media": ["part-size", "part-time", "slice"],
    "ocr": ["scan"],
    "open": [],
    "video": ["frames", "locate-logo", "rm-logo"],
}

TYPE_DESCRIPTIONS = {
    "app": "Mở ứng dụng GUI (Trình phát video kép so sánh)",
    "audio": "Các tính năng xử lý âm thanh (tách audio WAV/MP3)",
    "dld": "Tải media đa nền tảng (YouTube, FB, TikTok, Douyin...) & cập nhật",
    "git": "Thao tác tự động hóa Git (commit & push)",
    "image": "Các tính năng xử lý hình ảnh (lật ảnh, xoay ảnh)",
    "media": "Xử lý media đa dụng (cắt slice, chia theo size/thời gian)",
    "ocr": "Nhận diện văn bản từ hình ảnh bằng PaddleOCR",
    "open": "Mở thư mục dự án trong IDE (VSCode/Antigravity) hoặc Explorer",
    "video": "Các tính năng xử lý video (xóa watermark/logo, trích xuất frames)",
}

PROMPT_PLAIN = "mda > "
PROMPT_COLORED = "\033[38;5;45;1mmda\033[0m \033[38;5;214;1m>\033[0m "


def ensure_utf8_stdout():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# Thuật toán Auto-Complete & Cycle
# ---------------------------------------------------------------------------
def get_tab_completion(
    buffer: str, last_was_tab: bool, original_prefix: str, cycle_idx: int
) -> tuple[str, str, int, bool]:
    """
    Tính toán gợi ý hoàn thành / xoay vòng Tab dựa trên buffer hiện tại.
    Trả về: (new_buffer, original_prefix, cycle_idx, is_completed)
    """
    sorted_types = sorted(TYPE_ACTION_MAP.keys())

    # NGỮ CẢNH 1: Đang ở Token 0 (Nhóm lệnh - Type)
    if " " not in buffer:
        cleaned_buf = buffer.strip().lower()
        if not last_was_tab:
            if cleaned_buf in sorted_types:
                # Nếu đã là 1 type hợp lệ, chuẩn bị xoay vòng sang type tiếp theo
                original_prefix = ""
                candidates = sorted_types
                cycle_idx = (sorted_types.index(cleaned_buf) + 1) % len(sorted_types)
                return candidates[cycle_idx], original_prefix, cycle_idx, True
            else:
                original_prefix = cleaned_buf
                cycle_idx = 0
        else:
            cycle_idx += 1

        candidates = [t for t in sorted_types if t.startswith(original_prefix)]
        if not candidates:
            return buffer, original_prefix, cycle_idx, False

        cycle_idx = cycle_idx % len(candidates)
        chosen = candidates[cycle_idx]
        return chosen, original_prefix, cycle_idx, True

    # NGỮ CẢNH 2: Đã có Type -> Đang ở Token 1 (Hành động - Action) hoặc các tham số sau
    parts = buffer.split(" ")
    cmd_type = parts[0].strip().lower()

    if cmd_type not in TYPE_ACTION_MAP:
        return buffer, original_prefix, cycle_idx, False

    valid_actions = sorted(TYPE_ACTION_MAP.get(cmd_type, []))
    if not valid_actions:
        return buffer, original_prefix, cycle_idx, False

    action_part = parts[1].strip().lower() if len(parts) > 1 else ""
    rest_of_args = (" " + " ".join(parts[2:])) if len(parts) > 2 else ""

    if not last_was_tab:
        if action_part in valid_actions:
            # Nếu đã là 1 action hợp lệ, xoay vòng sang action tiếp theo
            original_prefix = ""
            candidates = valid_actions
            cycle_idx = (valid_actions.index(action_part) + 1) % len(valid_actions)
            chosen_action = candidates[cycle_idx]
            new_buffer = f"{cmd_type} {chosen_action}{rest_of_args}"
            return new_buffer, original_prefix, cycle_idx, True
        else:
            original_prefix = action_part
            cycle_idx = 0
    else:
        cycle_idx += 1

    candidates = [a for a in valid_actions if a.startswith(original_prefix)]
    if not candidates:
        return buffer, original_prefix, cycle_idx, False

    cycle_idx = cycle_idx % len(candidates)
    chosen_action = candidates[cycle_idx]
    new_buffer = f"{cmd_type} {chosen_action}{rest_of_args}"
    return new_buffer, original_prefix, cycle_idx, True


# ---------------------------------------------------------------------------
# Định dạng màu cho chuỗi lệnh trên dòng nhập
# ---------------------------------------------------------------------------
def format_buffer_colored(buffer: str) -> str:
    if not buffer:
        return ""

    parts = buffer.split(" ")
    if len(parts) == 1:
        cmd_type = parts[0]
        if cmd_type.lower() in TYPE_ACTION_MAP:
            return f"\033[32;1m{cmd_type}\033[0m"
        return f"\033[37m{cmd_type}\033[0m"
    elif len(parts) == 2:
        cmd_type, cmd_action = parts[0], parts[1]
        type_str = (
            f"\033[32;1m{cmd_type}\033[0m"
            if cmd_type.lower() in TYPE_ACTION_MAP
            else f"\033[37m{cmd_type}\033[0m"
        )
        valid_actions = TYPE_ACTION_MAP.get(cmd_type.lower(), [])
        action_str = (
            f"\033[36;1m{cmd_action}\033[0m"
            if cmd_action.lower() in valid_actions
            else f"\033[37m{cmd_action}\033[0m"
        )
        return f"{type_str} {action_str}"
    else:
        cmd_type, cmd_action = parts[0], parts[1]
        rest = " ".join(parts[2:])
        type_str = (
            f"\033[32;1m{cmd_type}\033[0m"
            if cmd_type.lower() in TYPE_ACTION_MAP
            else f"\033[37m{cmd_type}\033[0m"
        )
        valid_actions = TYPE_ACTION_MAP.get(cmd_type.lower(), [])
        action_str = (
            f"\033[36;1m{cmd_action}\033[0m"
            if cmd_action.lower() in valid_actions
            else f"\033[37m{cmd_action}\033[0m"
        )
        return f"{type_str} {action_str} \033[37m{rest}\033[0m"


# ---------------------------------------------------------------------------
# Bắt phím mức thấp trên Windows (msvcrt)
# ---------------------------------------------------------------------------
def autocomplete_input(prompt: str = PROMPT_COLORED) -> str | None:
    try:
        import msvcrt

        if not sys.stdin.isatty():
            try:
                line = sys.stdin.readline()
                if not line:
                    return None
                return line.rstrip("\r\n")
            except (KeyboardInterrupt, EOFError):
                return None
    except ImportError:
        # Fallback an toàn cho môi trường không phải Windows
        try:
            return input(PROMPT_PLAIN)
        except (KeyboardInterrupt, EOFError):
            return None

    buffer = ""
    last_was_tab = False
    original_prefix = ""
    cycle_idx = 0

    sys.stdout.write(prompt)
    sys.stdout.flush()

    while True:
        try:
            ch = msvcrt.getwch()
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            return None

        # Enter
        if ch in ("\r", "\n"):
            sys.stdout.write("\n")
            sys.stdout.flush()
            return buffer

        # Tab
        elif ch == "\t":
            new_buf, original_prefix, cycle_idx, ok = get_tab_completion(
                buffer, last_was_tab, original_prefix, cycle_idx
            )
            last_was_tab = True
            if ok:
                buffer = new_buf
                sys.stdout.write(f"\r\033[K{prompt}{format_buffer_colored(buffer)}")
                sys.stdout.flush()

        # Backspace
        elif ch in ("\x08", "\x7f"):
            last_was_tab = False
            original_prefix = ""
            cycle_idx = 0
            if len(buffer) > 0:
                buffer = buffer[:-1]
                sys.stdout.write(f"\r\033[K{prompt}{format_buffer_colored(buffer)}")
                sys.stdout.flush()

        # Ctrl+C, Ctrl+D
        elif ch in ("\x03", "\x04"):
            sys.stdout.write("\n")
            sys.stdout.flush()
            return None

        # Esc
        elif ch == "\x1b":
            if buffer:
                buffer = ""
                last_was_tab = False
                original_prefix = ""
                cycle_idx = 0
                sys.stdout.write(f"\r\033[K{prompt}")
                sys.stdout.flush()
            else:
                sys.stdout.write("\n")
                return None

        # Special prefix (Arrow keys, F-keys, etc.)
        elif ch in ("\x00", "\xe0"):
            try:
                msvcrt.getwch()  # Nuốt scan code phụ
            except Exception:
                pass

        # Printable character
        elif ch.isprintable():
            last_was_tab = False
            original_prefix = ""
            cycle_idx = 0
            buffer += ch
            sys.stdout.write(f"\r\033[K{prompt}{format_buffer_colored(buffer)}")
            sys.stdout.flush()


# ---------------------------------------------------------------------------
# In bảng tổng quan Types
# ---------------------------------------------------------------------------
def print_types_overview():
    print()
    print("\033[36;1m=== DANH SÁCH CÁC NHÓM LỆNH (TYPES) HIỆN CÓ ===\033[0m")
    print("\033[90m" + "─" * 70 + "\033[0m")
    for cmd_type in sorted(TYPE_ACTION_MAP.keys()):
        desc = TYPE_DESCRIPTIONS.get(cmd_type, "")
        actions = TYPE_ACTION_MAP[cmd_type]
        actions_str = ", ".join(actions) if actions else "(không có action)"
        print(f"  \033[32;1m{cmd_type:<8}\033[0m │ \033[37m{desc}\033[0m")
        print(f"           └── \033[90mactions:\033[0m \033[36m{actions_str}\033[0m")
    print("\033[90m" + "─" * 70 + "\033[0m")
    print(
        "💡 \033[33mGợi ý:\033[0m Nhập '\033[36mhelp\033[0m' hoặc '\033[36mh\033[0m' để xem toàn bộ tài liệu chi tiết."
    )
    print(
        "          Nhấn \033[35;1m[Tab]\033[0m để tự động điền / xoay vòng Type & Action, nhập '\033[31mq\033[0m' hoặc '\033[31mexit\033[0m' để thoát."
    )
    print()


# ---------------------------------------------------------------------------
# Quản lý phiên làm việc tương tác (REPL Controller)
# ---------------------------------------------------------------------------
def run_interactive_session():
    ensure_utf8_stdout()
    print_types_overview()

    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_py_path = os.path.join(src_dir, "main.py")

    while True:
        try:
            line = autocomplete_input()
            if line is None:
                print(">>> Tạm biệt!")
                break

            line = line.strip()
            if not line:
                continue

            # Lệnh tiện ích nội bộ session
            if line.lower() in ("q", "quit", "exit"):
                print(">>> Tạm biệt!")
                break

            if line.lower() in ("h", "help"):
                help_path = os.path.join(src_dir, "contents", "help.txt")
                if os.path.exists(help_path):
                    with open(help_path, "r", encoding="utf-8") as f:
                        print(f.read())
                else:
                    print("Không tìm thấy file help.txt")
                continue

            if line.lower() in ("type", "types", "list", "ls"):
                print_types_overview()
                continue

            if line.lower() in ("cls", "clear"):
                os.system("cls" if os.name == "nt" else "clear")
                print_types_overview()
                continue

            # Tự động loại bỏ từ khóa 'mda' nếu người dùng lỡ gõ
            if line.startswith("mda "):
                line = line[4:].strip()

            try:
                args = shlex.split(line, posix=False)
            except Exception as parse_err:
                print(f">>> Lỗi cú pháp lệnh: {parse_err}")
                continue

            if not args:
                continue

            # Gọi subprocess main.py để thực thi lệnh một cách an toàn và độc lập
            cmd = [sys.executable, main_py_path] + args
            try:
                subprocess.run(cmd)
            except KeyboardInterrupt:
                print("\n>>> Lệnh đã bị hủy bởi người dùng.")
            except Exception as exec_err:
                print(f">>> Lỗi thực thi: {exec_err}")

            print()

        except KeyboardInterrupt:
            print("\n>>> Nhập 'q' hoặc 'exit' để thoát phiên tương tác.")
        except EOFError:
            print("\n>>> Tạm biệt!")
            break


if __name__ == "__main__":
    run_interactive_session()
