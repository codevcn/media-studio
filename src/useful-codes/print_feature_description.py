import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/D-Documents/TOOLs/media-studio/.env")

ROOT_FOLDER_PATH = os.getenv("ROOT_FOLDER_PATH") or ""


def get_script_path(relative_path: str) -> str:
    """Trả về absolute path của script con dựa theo file hiện tại"""
    # This script is in src/useful-codes, so relative to src is one level up
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(src_dir, relative_path)


def print_feature_description(cmd_type: str, cmd_action: str):
    yml_path = get_script_path("contents/app_features.yml")
    if not os.path.exists(yml_path):
        print(f">>> Warn: Không tìm thấy file {yml_path}")
        sys.exit(1)

    try:
        import yaml
    except ImportError:
        print(
            ">>> Warn: Yêu cầu cài đặt thư viện 'PyYAML' (pip install PyYAML) để dùng --des"
        )
        sys.exit(1)

    with open(yml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    types = data.get("mdia_tool", {}).get("types", [])
    for t in types:
        if t.get("name") == cmd_type:
            actions = t.get("actions", [])
            for action in actions:
                command_str = action.get("command", "")

                # Check nếu action khớp pattern
                if cmd_action:
                    match_str = f"mdia {cmd_type} {cmd_action}"
                else:
                    match_str = f"mdia {cmd_type}"

                if match_str in command_str:
                    if hasattr(sys.stdout, "reconfigure"):
                        getattr(sys.stdout, "reconfigure")(encoding="utf-8")
                    print(
                        "=================================================================="
                    )
                    print(f"[{action.get('id')}] {action.get('title')}")
                    print(f"Lệnh    : {action.get('command')}")
                    print(f"Tóm tắt : {action.get('summary')}")
                    print(f"Chi tiết: {action.get('details')}")
                    print(f"Yêu cầu : {action.get('conditions')}")
                    print(
                        "=================================================================="
                    )
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
