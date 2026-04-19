import os
import sys
import subprocess
import datetime


def parse_gap_to_ms(gap_str: str) -> int:
    gap_str = gap_str.strip().lower()
    try:
        if gap_str.endswith("ms"):
            return int(float(gap_str[:-2]))
        elif gap_str.endswith("s"):
            return int(float(gap_str[:-1]) * 1000)
        elif gap_str.endswith("m") or gap_str.endswith("p"):
            return int(float(gap_str[:-1]) * 60 * 1000)
        elif gap_str.endswith("h"):
            return int(float(gap_str[:-1]) * 3600 * 1000)
        else:
            return int(float(gap_str))
    except ValueError:
        raise ValueError(f"Không thể phân tích trị thời gian gap: '{gap_str}'")


def extract_frames(input_file: str, gap_time: str, limit: int = 0) -> None:
    # --- Validate file ---
    if not os.path.isfile(input_file):
        print(f"[ERROR] Không tìm thấy file: {input_file}")
        sys.exit(1)

    try:
        gap_ms = parse_gap_to_ms(gap_time)
        if gap_ms <= 0:
            raise ValueError
    except ValueError as e:
        print(f"[ERROR] Thời gian giãn cách không hợp lệ: {e}")
        sys.exit(1)

    # --- Tạo thư mục output chứa các frames ---
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    input_dir = os.path.dirname(os.path.abspath(input_file))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{base_name}--frames--{timestamp}"
    output_dir = os.path.join(input_dir, folder_name)

    os.makedirs(output_dir, exist_ok=True)

    # Tính toán số khung hình mỗi giây (fps) từ số mili-giây (gap)
    # Ví dụ gap_ms = 500 => fps = 1000 / 500 = 2 khung hình / 1 giây
    fps_val = 1000.0 / gap_ms

    # Định dạng ảnh xuất ra là PNG.
    # Giải thích: PNG là định dạng tốt nhất để trích xuất frame vì nó áp dụng thuật toán
    # nén không mất dữ liệu (lossless). Hình ảnh sẽ giữ nguyên trọn vẹn từng pixel như clip gốc
    # khác xa với chuẩn JPG dễ bị nhiễu do nén (lossy).
    output_pattern = os.path.join(output_dir, "frame_%05d.png")

    print(f"[INFO] Input          : {input_file}")
    print(f"[INFO] Thư mục lưu    : {output_dir}")
    print(
        f"[INFO] Khoảng cách    : {gap_time} (~{gap_ms} ms) (Quy đổi: {fps_val:.2f} fps)"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vf",
        f"fps={fps_val}",
    ]

    if limit > 0:
        cmd.extend(["-vframes", str(limit)])
        print(f"[INFO] Giới hạn       : {limit} frame(s)")

    cmd.append(output_pattern)

    print(f"Bắt đầu trích xuất, vui lòng chờ...")

    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print(f"[ERROR] ffmpeg xử lý thất bại:\n{result.stderr}")
        sys.exit(1)

    files_created = [f for f in os.listdir(output_dir) if f.endswith(".png")]
    print(
        f"[DONE] Đã trích xuất thành công {len(files_created)} frame(s) ra định dạng chất lượng cao (PNG)."
    )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Sử dụng: python extract_frames.py <input_path> <gap_time> [limit]")
        print("Ví dụ:   python extract_frames.py video.mp4 5s 50")
        print("         python extract_frames.py video.mp4 200ms")
        sys.exit(1)

    input_file = sys.argv[1]
    gap_time = sys.argv[2]

    limit_val = 0
    if len(sys.argv) >= 4:
        try:
            limit_val = int(sys.argv[3])
        except ValueError:
            pass

    extract_frames(input_file, gap_time, limit_val)
