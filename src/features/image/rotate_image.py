import sys
from pathlib import Path
from PIL import Image


def ensure_utf8_stdout() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")


def print_usage() -> None:
    script_name = Path(sys.argv[0]).name
    print("Sử dụng:")
    print(f'  python {script_name} "ABSOLUTE_INPUT_IMAGE_PATH" <degrees> [output_path]')
    print()
    print("Ví dụ:")
    print(f'  python {script_name} "D:\\data\\image.jpg" 90')
    print(
        f'  python {script_name} "D:\\data\\image.jpg" -45 "D:\\data\\image_rotated.jpg"'
    )


def build_default_output_path(input_path: Path, degrees: float) -> Path:
    deg_str = (
        str(degrees).rstrip("0").rstrip(".") if "." in str(degrees) else str(degrees)
    )
    return input_path.with_name(
        f"{input_path.stem}_rotate-{deg_str}deg{input_path.suffix}"
    )


def rotate_image(
    input_image_path: str, degrees: str | float, output_image_path: str | None = None
) -> Path:
    ensure_utf8_stdout()

    input_path = Path(input_image_path)
    try:
        degrees_val = float(degrees)
    except ValueError:
        raise ValueError(f"Giá trị xoay '{degrees}' không hợp lệ. Phải là một số.")

    if not input_path.is_absolute():
        raise ValueError(f"Input path phải là absolute path: {input_path}")

    if not input_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file ảnh đầu vào: {input_path}")

    if input_path.is_dir():
        raise ValueError(
            f"Input path phải là file ảnh, không phải thư mục: {input_path}"
        )

    output_path = (
        Path(output_image_path)
        if output_image_path
        else build_default_output_path(input_path, degrees_val)
    )

    if not output_path.is_absolute():
        raise ValueError(f"Output path phải là absolute path: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(input_path) as image:
        # Pillow rotate is counter-clockwise. Negative value rotates clockwise.
        # expand=True ensures the image canvas expands to fit the rotated image
        rotated = image.rotate(degrees_val, expand=True)
        rotated.save(output_path)

    print(f"Đã xoay ảnh {degrees_val} độ: {output_path}")
    return output_path


if __name__ == "__main__":
    ensure_utf8_stdout()

    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    input_file = sys.argv[1]
    rotate_deg = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        rotate_image(input_file, rotate_deg, output_file)
    except Exception as e:
        print(f">>> Lỗi: {e}")
        sys.exit(1)
