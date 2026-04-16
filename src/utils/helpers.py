import json
from pathlib import Path

def get_project_root() -> Path:
    """
    Trả về đường dẫn tuyệt đối đến thư mục gốc của dự án.
    Giả định file hiện tại nằm ở: src/utils/helpers.py
    Thư mục gốc sẽ là thư mục chứa thư mục 'src'.
    """
    return Path(__file__).resolve().parent.parent.parent

def load_configs(config_path: str = "src/configs/configs.json") -> dict:
    """
    Đọc cấu hình từ file JSON.
    Hỗ trợ tham số đường dẫn tương đối từ thư mục gốc của dự án.
    """
    root_dir = get_project_root()
    full_config_path = root_dir / config_path
    
    if not full_config_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file cấu hình tại: {full_config_path}")
        
    with open(full_config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
        
    return config_data

def resolve_path(relative_path: str) -> Path:
    """
    Chuyển đổi đường dẫn tương đối (từ gốc dự án) thành đường dẫn tuyệt đối.
    """
    root_dir = get_project_root()
    return root_dir / relative_path

if __name__ == "__main__":
    # Test file
    try:
        configs = load_configs()
        print("=== DỮ LIỆU CONFIG ĐÃ ĐỌC ===")
        print(json.dumps(configs, indent=2, ensure_ascii=False))
        
        # Test việc tạo đường dẫn tuyệt đối cho các path trong config
        if "videos" in configs and len(configs["videos"]) > 0:
            first_video = configs["videos"][0]
            input_path = first_video.get("input_path")
            output_path = first_video.get("output_path")
            
            print("\n=== ĐƯỜNG DẪN TUYỆT ĐỐI TƯƠNG ỨNG ===")
            print(f"Input path:  {resolve_path(input_path)}")
            print(f"Output path: {resolve_path(output_path)}")
            
    except Exception as e:
        print(f"Lỗi: {e}")
