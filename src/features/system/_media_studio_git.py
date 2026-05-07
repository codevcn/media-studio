import sys
import os
import subprocess

# Đảm bảo src directory nằm trong sys.path để import configs
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from configs.paths import ROOT_FOLDER_PATH


def git_commit_and_push(message: str):
    if not message:
        print(">>> Lỗi: Thông điệp commit không được để trống!")
        sys.exit(1)

    print(f"=== Bắt đầu đóng gói và tải code (Commit & Push) ===")
    print(f"Thư mục làm việc: {ROOT_FOLDER_PATH}")
    print(f"Commit Message  : {message}")

    print("\n[1/3] Đang thêm file vào staging (git add .)...")
    subprocess.run(["git", "add", "."], cwd=ROOT_FOLDER_PATH)

    print("\n[2/3] Đang ghi nhận các thay đổi (git commit)...")
    subprocess.run(["git", "commit", "-m", message], cwd=ROOT_FOLDER_PATH)

    print("\n[3/3] Đang đẩy lên máy chủ mã nguồn (git push origin main)...")
    result = subprocess.run(["git", "push", "origin", "main"], cwd=ROOT_FOLDER_PATH)

    if result.returncode == 0:
        print("\n=== Hoàn tất thành công! ===")
    else:
        print("\n>>> Cảnh báo: Quá trình push (hoặc commit) có thể đã gặp lỗi.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Sử dụng: python _media_studio_git.py <action> <message>")
        sys.exit(1)

    action = sys.argv[1]
    message = sys.argv[2]

    if action == "commit":
        git_commit_and_push(message)
    else:
        print(f">>> Lỗi: Hành động git không được hỗ trợ '{action}'")
        sys.exit(1)
