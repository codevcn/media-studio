import sys
from pathlib import Path

from PIL import Image


SUPPORTED_DIRECTIONS = {
    "horizontal": Image.Transpose.FLIP_LEFT_RIGHT,
    "h": Image.Transpose.FLIP_LEFT_RIGHT,
    "ngang": Image.Transpose.FLIP_LEFT_RIGHT,
    "vertical": Image.Transpose.FLIP_TOP_BOTTOM,
    "v": Image.Transpose.FLIP_TOP_BOTTOM,
    "doc": Image.Transpose.FLIP_TOP_BOTTOM,
}
CANONICAL_DIRECTIONS = {
    "horizontal": "horizontal",
    "h": "horizontal",
    "ngang": "horizontal",
    "vertical": "vertical",
    "v": "vertical",
    "doc": "vertical",
}


def ensure_utf8_stdout() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")


def print_usage() -> None:
    script_name = Path(sys.argv[0]).name
    print("Sử dụng:")
    print(f'  python {script_name} "ABSOLUTE_INPUT_IMAGE_PATH" <horizontal|vertical> [output_path]')
    print()
    print("Ví dụ:")
    print(f'  python {script_name} "D:\\data\\image.jpg" horizontal')
    print(f'  python {script_name} "D:\\data\\image.jpg" vertical "D:\\data\\image_flipped.jpg"')


def build_default_output_path(input_path: Path, direction: str) -> Path:
    return input_path.with_name(f"{input_path.stem}_flip-{direction}{input_path.suffix}")


def flip_image(input_image_path: str, direction: str, output_image_path: str | None = None) -> Path:
    ensure_utf8_stdout()

    input_path = Path(input_image_path)
    normalized_direction = direction.strip().lower()

    if not input_path.is_absolute():
        raise ValueError(f"Input path phải là absolute path: {input_path}")

    if not input_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file ảnh đầu vào: {input_path}")

    if input_path.is_dir():
        raise ValueError(f"Input path phải là file ảnh, không phải thư mục: {input_path}")

    if normalized_direction not in SUPPORTED_DIRECTIONS:
        raise ValueError("Hướng lật không hợp lệ. Vui lòng dùng horizontal hoặc vertical.")

    canonical_direction = CANONICAL_DIRECTIONS[normalized_direction]
    output_path = (
        Path(output_image_path)
        if output_image_path
        else build_default_output_path(input_path, canonical_direction)
    )

    if not output_path.is_absolute():
        raise ValueError(f"Output path phải là absolute path: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(input_path) as image:
        flipped = image.transpose(SUPPORTED_DIRECTIONS[normalized_direction])
        flipped.save(output_path)

    print(f"Đã lật ảnh theo chiều {canonical_direction}: {output_path}")
    return output_path


if __name__ == "__main__":
    ensure_utf8_stdout()

    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    input_file = sys.argv[1]
    flip_direction = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        flip_image(input_file, flip_direction, output_file)
    except Exception as e:
        print(f">>> Lỗi: {e}")
        sys.exit(1)
