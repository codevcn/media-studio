import os
import subprocess


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
                command, check=True, capture_output=True, text=True
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
    # Khai báo đường dẫn tập tin đầu vào và đầu ra
    # Đảm bảo video clip_2phut_dau.mp4 nằm cùng thư mục với script này
    input_video = "clip_2phut_dau.mp4"
    output_video = "clip_2phut_dau_nologo.mp4"

    try:
        # Khởi tạo công cụ xóa logo
        remover = FFmpegLogoRemover(input_path=input_video, output_path=output_video)

        # Điền các thông số bạn đã đo được ở Bước 1
        # Thay thế các giá trị bên dưới bằng con số chính xác của bạn
        x_coord = 24
        y_coord = 21
        width = 135
        height = 44

        print("Bắt đầu tiến trình xóa watermark...")

        # Gọi hàm xóa logo
        # Bạn có thể giữ nguyên preset="faster" và crf=23 như mặc định của class
        remover.remove_logo(
            x=x_coord, y=y_coord, w=width, h=height, preset="faster", crf=23
        )

    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")


if __name__ == "__main__":
    main()
