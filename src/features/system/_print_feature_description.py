import os
import sys
import argparse
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
    "spotify",
}


def get_script_path(relative_path: str) -> str:
    """Trả về absolute path của script con dựa theo file hiện tại"""
    # This script is in src/useful-codes, so relative to src is one level up
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(src_dir, relative_path)


def get_content_path(filename: str) -> str:
    contents_dir = CONTENTS_FOLDER_PATH or get_script_path("contents")
    return os.path.join(contents_dir, filename)


def ensure_utf8_stdout():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")


def is_command_match(command_str: str, cmd_type: str, cmd_action: str) -> bool:
    if cmd_action:
        match_str = f"mda {cmd_type} {cmd_action}"
    else:
        match_str = f"mda {cmd_type}"

    if match_str in command_str:
        return True

    return (
        cmd_type == "dld"
        and cmd_action in DLD_PLATFORM_ALIASES
        and "mda dld <platform>" in command_str
    )


def print_feature_description(cmd_type: str, cmd_action: str):
    ensure_utf8_stdout()

    yml_path = get_content_path("app_features.yml")
    if not os.path.exists(yml_path):
        print(f">>> Warn: Không tìm thấy file {yml_path}")
        sys.exit(1)

    with open(yml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    types = data.get("mdia_tool", {}).get("types", [])
    for t in types:
        if t.get("name") == cmd_type:
            actions = t.get("actions", [])
            for action in actions:
                command_str = action.get("command", "")

                if is_command_match(command_str, cmd_type, cmd_action):
                    print(Fore.CYAN + Style.BRIGHT + "==================================================================")
                    print(Fore.CYAN + Style.BRIGHT + f"[{action.get('id')}] {action.get('title')}")
                    print(Fore.YELLOW + "Lệnh      : " + Fore.WHITE + f"{action.get('command')}")
                    print(Fore.YELLOW + "Tóm tắt   : " + Fore.WHITE + f"{action.get('summary')}")
                    print(Fore.YELLOW + "Chi tiết  : " + Fore.WHITE + f"{action.get('details')}")
                    print(Fore.YELLOW + "Tham số   : " + Fore.WHITE + f"{action.get('parameters', 'Không có')}")
                    print(Fore.YELLOW + "Yêu cầu   : " + Fore.WHITE + f"{action.get('conditions')}")
                    print(Fore.CYAN + Style.BRIGHT + "==================================================================")
                    sys.exit(0)

            print(
                f">>> Warn: Mặc dù loại lệnh '{cmd_type}' tồn tại nhưng không tìm thấy mô tả cho (action={cmd_action})."
            )
            sys.exit(1)

    print(f">>> Warn: Không tìm thấy loại lệnh '{cmd_type}' trong file cấu hình.")
    sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", type=str, required=True)
    parser.add_argument("--action", type=str, default="")
    args = parser.parse_args()

    print_feature_description(args.type, args.action)
