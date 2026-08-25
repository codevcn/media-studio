import sys
import os
import argparse

# Cấu hình biến môi trường trước khi import paddleocr để tránh lỗi PIR/MKLDNN trên Paddle 3.0+
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"

from paddleocr import PaddleOCR

def ensure_utf8_stdout():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

def main():
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description="Scan OCR using PaddleOCR")
    parser.add_argument("input_path", type=str, help="Path to the image file")
    parser.add_argument("--output", type=str, choices=["log", "file"], default="log", help="Output destination")
    parser.add_argument("--dest", type=str, default=None, help="Destination file path if output is file")
    
    args = parser.parse_args()

    input_path = args.input_path
    output_mode = args.output
    dest_path = args.dest

    # Validate inputs
    if not os.path.exists(input_path):
        print(f">>> Lỗi: File ảnh không tồn tại: {input_path}")
        sys.exit(1)
        
    if not os.path.isfile(input_path):
        print(f">>> Lỗi: Đường dẫn không phải là một file hợp lệ: {input_path}")
        sys.exit(1)

    if output_mode == "file" and not dest_path:
        print(">>> Lỗi: Phải chỉ định cờ --dest khi chọn --output=file")
        sys.exit(1)

    if output_mode == "file":
        dest_dir = os.path.dirname(dest_path)
        if dest_dir and not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir, exist_ok=True)
            except Exception as e:
                print(f">>> Lỗi: Không thể tạo thư mục đích {dest_dir}: {e}")
                sys.exit(1)

    print(">>> Đang khởi tạo PaddleOCR (có thể mất một lúc ở lần chạy đầu tiên)...")
    try:
        # Bổ sung enable_mkldnn=False để fix lỗi "ConvertPirAttribute2RuntimeAttribute not support" trên một số bản PaddlePaddle mới dùng CPU
        ocr = PaddleOCR(use_textline_orientation=True, lang="en", enable_mkldnn=False) # Hỗ trợ tiếng anh
    except Exception as e:
        print(f">>> Lỗi khi khởi tạo PaddleOCR: {e}")
        sys.exit(1)

    print(f">>> Đang quét ảnh: {input_path}")
    try:
        # Trong các bản PaddleOCR mới, hàm ocr bị báo deprecate và khuyên dùng predict
        # cls parameter cũng có thể không còn được hỗ trợ trong hàm dự đoán
        result = ocr.predict(input_path)
    except Exception as e:
        try:
            # Fallback nếu predict có vấn đề
            result = ocr.ocr(input_path)
        except Exception as ex:
            print(f">>> Lỗi trong quá trình quét ảnh: {e} | {ex}")
            sys.exit(1)

    if not result or result[0] is None:
        print(">>> Không tìm thấy text nào trong ảnh.")
        sys.exit(0)

    # Extract text from result
    # result is a list of lists: [[[[x, y], [x, y], [x, y], [x, y]], ('text', confidence)], ...]
    extracted_text = []
    for idx in range(len(result)):
        res = result[idx]
        if res is not None:
            for line in res:
                extracted_text.append(line[1][0])

    final_text = "\n".join(extracted_text)

    if output_mode == "log":
        print("\n--- KẾT QUẢ OCR ---")
        print(final_text)
        print("-------------------\n")
        print(">>> Hoàn tất.")
    elif output_mode == "file":
        try:
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(final_text)
            print(f">>> Đã lưu kết quả OCR vào file: {dest_path}")
        except Exception as e:
            print(f">>> Lỗi khi ghi file: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
