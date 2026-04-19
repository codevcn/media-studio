import os
import subprocess
import sys


class FFmpegLogoRemover:
    def __init__(self, input_path: str, output_path: str):
        """
        Khởi tạo lớp xử lý xóa logo video bằng FFmpeg.

        :param input_path: Đường dẫn đến tập tin video gốc.
        :param output_path: Đường dẫn lưu tập tin video sau khi xử lý.
        """
        self.input_path = input_path
        self.output_path = output_path

        if not os.path.exists(self.input_path):
            raise FileNotFoundError(
                f"Không tìm thấy tập tin video đầu vào tại đường dẫn: {self.input_path}"
            )

    def remove_logo(
        self, x: int, y: int, w: int, h: int, preset: str = "faster", crf: int = 23
    ):
        """
        Thực thi lệnh xóa logo bằng bộ lọc 'delogo' của FFmpeg với các tham số tối ưu.

        :param x, y: Tọa độ góc trên cùng bên trái của vùng chứa logo.
        :param w, h: Chiều rộng và chiều cao của vùng chứa logo.
        :param preset: Tốc độ mã hóa video của FFmpeg (ultrafast, superfast, veryfast, faster, fast, medium).
                       Tốc độ càng nhanh thì dung lượng tập tin có thể lớn hơn một chút.
        :param crf: Chỉ số nén chất lượng video (Constant Rate Factor). Giá trị từ 0 đến 51.
                    Mức 23 là mức cân bằng hoàn hảo giữa chất lượng và dung lượng cho video MP4.
        """
        print("Bắt đầu quá trình xử lý video bằng FFmpeg...")

        # Xây dựng câu lệnh FFmpeg với các tham số tối ưu hóa
        command = [
            "ffmpeg",
            "-y",  # Đồng ý ghi đè nếu tập tin đầu ra đã tồn tại
            "-hwaccel",
            "auto",  # Tự động sử dụng phần cứng (GPU) để tăng tốc nếu hệ thống hỗ trợ
            "-i",
            self.input_path,  # Đường dẫn tập tin đầu vào
            "-vf",
            f"delogo=x={x}:y={y}:w={w}:h={h}",  # Sử dụng bộ lọc xóa logo
            "-c:v",
            "libx264",  # Khai báo bộ mã hóa video chuẩn H.264
            "-preset",
            preset,  # Thiết lập tốc độ mã hóa để tiết kiệm thời gian
            "-crf",
            str(crf),  # Thiết lập chất lượng video đầu ra
            "-c:a",
            "copy",  # Sao chép trực tiếp luồng âm thanh, không mã hóa lại để giữ nguyên chất lượng
            self.output_path,  # Đường dẫn tập tin đầu ra
        ]

        try:
            # Thực thi câu lệnh và chờ quá trình hoàn tất
            # Đặt capture_output=True để thu thập log, giúp màn hình console gọn gàng hơn
            process = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            print("-" * 50)
            print(f"Hoàn tất! Video đã được xử lý thành công.")
            print(f"Video đầu ra được lưu tại: {self.output_path}")
            print("-" * 50)

        except FileNotFoundError:
            print(
                "Lỗi hệ thống: Không tìm thấy phần mềm FFmpeg. Vui lòng kiểm tra lại quá trình cài đặt FFmpeg trên máy tính của bạn."
            )
        except subprocess.CalledProcessError as e:
            print("Đã xảy ra lỗi trong quá trình thực thi FFmpeg:")
            print(e.stderr)  # In ra chi tiết lỗi từ FFmpeg để dễ dàng khắc phục


def main():
    if len(sys.argv) < 3:
        print(
            "Sử dụng: python video_watermark_remover.py <input_path> <x,y,w,h> [output_path]"
        )
        sys.exit(1)

    input_video = sys.argv[1]
    box_coords = sys.argv[2].split(",")

    if len(box_coords) != 4:
        print("Lỗi: Tọa độ phải có định dạng x,y,w,h (ví dụ: 24,21,135,44)")
        sys.exit(1)

    try:
        x_coord = int(box_coords[0].strip())
        y_coord = int(box_coords[1].strip())
        width = int(box_coords[2].strip())
        height = int(box_coords[3].strip())
    except ValueError:
        print("Lỗi: Tọa độ phải là các số nguyên âm.")
        sys.exit(1)

    if len(sys.argv) >= 4 and sys.argv[3].strip():
        output_video = sys.argv[3].strip()
    else:
        # Default output video name
        base_name, ext = os.path.splitext(input_video)
        output_video = f"{base_name}_no-logo{ext}"

    try:
        # Khởi tạo công cụ xóa logo
        remover = FFmpegLogoRemover(input_path=input_video, output_path=output_video)

        print(
            f"Bắt đầu tiến trình xóa watermark tại ({x_coord},{y_coord}) kích thước {width}x{height}..."
        )

        # Gọi hàm xóa logo
        remover.remove_logo(
            x=x_coord, y=y_coord, w=width, h=height, preset="faster", crf=23
        )

    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")


if __name__ == "__main__":
    main()
