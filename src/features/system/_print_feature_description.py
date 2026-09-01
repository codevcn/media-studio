import os
import sys
import argparse
from pathlib import Path
import yaml
from colorama import init, Fore, Style

# Đảm bảo src directory nằm trong sys.path để import configs
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from configs.paths import ROOT_FOLDER_PATH, CONTENTS_FOLDER_PATH

init(autoreset=True)

DLD_PLATFORM_ALIASES = {
    "ytb",
    "ytb-music",
    "fb",
    "insta",
    "tiktok",
    "douyin",
    "bilibili",
    "bili",
    "bilili",
    "soundcloud",
    "scloud",
    "spot",
    "spotify",
    "twitter",
    "x",
}

# ANSI Color codes
CYAN_BOLD = "\033[36;1m"
GREEN_BOLD = "\033[32;1m"
YELLOW = "\033[33m"
WHITE = "\033[97m"
DIM = "\033[2m"
GRAY = "\033[90m"
RESET = "\033[0m"


def get_script_path(relative_path: str) -> str:
    """Trả về absolute path của script con dựa theo file hiện tại"""
    src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(src_path, relative_path)


def get_content_path(filename: str) -> str:
    contents_dir = CONTENTS_FOLDER_PATH or get_script_path("contents")
    return os.path.join(contents_dir, filename)


def ensure_utf8_stdout():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")


def is_command_match(command_str: str, cmd_type: str, cmd_action: str) -> bool:
    if not command_str:
        return False

    sub_cmds = [c.strip() for c in command_str.split("|")]

    if cmd_action:
        target_str = f"mda {cmd_type} {cmd_action}"
        for sub_cmd in sub_cmds:
            tokens = sub_cmd.split()
            if len(tokens) >= 3 and tokens[0] == "mda" and tokens[1] == cmd_type and tokens[2] == cmd_action:
                return True
            if target_str in sub_cmd or sub_cmd.startswith(target_str):
                return True

        if cmd_type == "dld" and cmd_action in DLD_PLATFORM_ALIASES:
            for sub_cmd in sub_cmds:
                if "mda dld <platform>" in sub_cmd or f"mda dld {cmd_action}" in sub_cmd:
                    return True
        return False
    else:
        for sub_cmd in sub_cmds:
            tokens = sub_cmd.split()
            if tokens and tokens[0] == "mda" and len(tokens) > 1 and tokens[1] == cmd_type:
                # Chỉ khớp nếu lệnh không có action cụ thể mà chỉ có cờ tùy chọn
                if len(tokens) == 2 or (len(tokens) > 2 and tokens[2].startswith(("-", "[")) and not tokens[2].startswith("<")):
                    return True
        return False


def render_action_block(action: dict):
    # Kiểm tra raw_file
    raw_file = action.get("raw_file")
    if raw_file:
        candidate_paths = [
            Path(ROOT_FOLDER_PATH) / raw_file if ROOT_FOLDER_PATH else None,
            Path(src_dir) / raw_file,
            Path(src_dir).parent / raw_file,
            Path(raw_file),
        ]
        for cp in candidate_paths:
            if cp and cp.is_file():
                with open(cp, "r", encoding="utf-8", errors="replace") as f:
                    print(f"\n{f.read().strip()}\n")
                return

    # Kiểm tra raw_text
    raw_text = action.get("raw_text")
    if raw_text:
        print(f"\n{raw_text.strip()}\n")
        return

    # In dạng bảng màu ANSI chuẩn
    title = action.get("title", "Không có tiêu đề")
    act_id = action.get("id", "")
    id_badge = f" [{act_id}]" if act_id else ""

    print()
    print(f"{CYAN_BOLD}--- Tính năng: {title}{id_badge} ---{RESET}")
    print(f"{GREEN_BOLD}+) Lệnh:{RESET}\t{YELLOW}{action.get('command', 'Không có')}{RESET}")
    print(f"{GREEN_BOLD}+) Tóm tắt:{RESET}\t{WHITE}{action.get('summary', 'Không có')}{RESET}")
    print(f"{GREEN_BOLD}+) Chi tiết:{RESET}\t{DIM}{action.get('details', 'Không có')}{RESET}")

    if action.get("parameters"):
        print(f"{GREEN_BOLD}+) Tham số:{RESET}\t{WHITE}{action.get('parameters')}{RESET}")
    if action.get("flags"):
        print(f"{GREEN_BOLD}+) Flags:{RESET}\t{WHITE}{action.get('flags')}{RESET}")
    if action.get("conditions"):
        print(f"{GREEN_BOLD}+) Điều kiện:{RESET}\t{DIM}{action.get('conditions')}{RESET}")
    print()


def print_feature_description(cmd_type: str = None, cmd_action: str = None):
    ensure_utf8_stdout()

    yml_path = get_content_path("app_features.yml")
    if not os.path.exists(yml_path):
        print(f">>> Warn: Không tìm thấy file {yml_path}")
        sys.exit(0)

    try:
        with open(yml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f">>> Lỗi khi đọc file catalog {yml_path}: {e}")
        sys.exit(0)

    mdia_tool = data.get("mdia_tool", {})
    dispatcher_flags = mdia_tool.get("dispatcher_flags", [])
    types = mdia_tool.get("types", [])

    # =========================================================================
    # CẤP 1: Tra cứu cấp Toàn bộ tool (`mda --info`)
    # =========================================================================
    if not cmd_type and not cmd_action:
        print()
        print(f"{CYAN_BOLD}=================================================================={RESET}")
        print(f"{CYAN_BOLD}🚀 Media Studio CLI (mda) — Bộ Công Cụ Xử Lý Media Đa Năng{RESET}")
        print(f"{CYAN_BOLD}=================================================================={RESET}")
        print(f"{GREEN_BOLD}+) Cú pháp chung:{RESET} {YELLOW}mda <type> <action> [tham_số...] [flags]{RESET}")
        print(f"{GREEN_BOLD}+) Chế độ tương tác:{RESET} {WHITE}Chạy 'mda' không tham số để vào REPL + Tab Autocomplete.{RESET}")

        if dispatcher_flags:
            print()
            print(f"{CYAN_BOLD}Các cờ điều phối toàn cục (Dispatcher Flags):{RESET}")
            for df in dispatcher_flags:
                flag_str = df.get("flag", "")
                desc_str = df.get("description", "")
                print(f"  {YELLOW}{flag_str:<22}{RESET} : {WHITE}{desc_str}{RESET}")

        if types:
            print()
            print(f"{CYAN_BOLD}Danh sách nhóm lệnh (Types):{RESET}")
            for t in types:
                t_name = t.get("name", "")
                t_desc = t.get("description", "")
                print(f"  {GREEN_BOLD}{t_name:<10}{RESET} : {WHITE}{t_desc}{RESET}")

        print()
        print(f"💡 {YELLOW}Tra cứu chi tiết:{RESET} Gõ {YELLOW}mda <type> --info{RESET} hoặc {YELLOW}mda <type> <action> --info{RESET}")
        print(f"{CYAN_BOLD}=================================================================={RESET}")
        print()
        sys.exit(0)

    # Tìm type tương ứng
    target_type = None
    for t in types:
        if t.get("name") == cmd_type:
            target_type = t
            break

    if not target_type:
        print(f">>> Warn: Không tìm thấy loại lệnh '{cmd_type}' trong file cấu hình.")
        sys.exit(0)

    actions = target_type.get("actions", [])

    # =========================================================================
    # CẤP 2: Tra cứu cấp Type (`mda <type> --info`)
    # =========================================================================
    if cmd_type and not cmd_action:
        matched_action = None
        for a in actions:
            if is_command_match(a.get("command", ""), cmd_type, None):
                matched_action = a
                break

        if matched_action:
            render_action_block(matched_action)
            sys.exit(0)

        print()
        print(f"{CYAN_BOLD}=== NHÓM LỆNH: {cmd_type.upper()} ({target_type.get('description', '')}) ==={RESET}")
        print(f"{GRAY}" + "─" * 70 + f"{RESET}")
        for a in actions:
            title = a.get("title", "")
            cmd_ex = a.get("command", "")
            summary = a.get("summary", "")
            print(f"  {GREEN_BOLD}• {title}{RESET}")
            print(f"    {YELLOW}Lệnh:{RESET}    {cmd_ex}")
            print(f"    {WHITE}Tóm tắt:{RESET} {summary}")
            print()
        print(f"💡 {YELLOW}Xem chi tiết từng lệnh:{RESET} Gõ {YELLOW}mda {cmd_type} <action> --info{RESET}")
        print(f"{GRAY}" + "─" * 70 + f"{RESET}")
        print()
        sys.exit(0)

    # =========================================================================
    # CẤP 3: Tra cứu cấp Action (`mda <type> <action> --info`)
    # =========================================================================
    for a in actions:
        if is_command_match(a.get("command", ""), cmd_type, cmd_action):
            render_action_block(a)
            sys.exit(0)

    print(
        f">>> Warn: Mặc dù loại lệnh '{cmd_type}' tồn tại nhưng không tìm thấy mô tả cho action '{cmd_action}'."
    )
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", type=str, default=None)
    parser.add_argument("--action", type=str, default=None)
    args = parser.parse_args()

    print_feature_description(args.type, args.action)

