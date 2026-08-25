import json
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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

def clean_url(raw_url: str, platform: str | None = None) -> str:
    """
    Chuẩn hóa và làm sạch URL trước khi tải xuống:
    - Loại bỏ khoảng trắng thừa, dấu ngoặc kép / nháy đơn / dấu nháy ngược bao quanh.
    - Trích xuất URL hợp lệ nếu người dùng paste chuỗi chứa kèm văn bản chia sẻ.
    - Loại bỏ các tham số tracking (utm_*, fbclid, igsh, si, feature, v.v.).
    - Loại bỏ các tham số playlist động/radio (list=RD*, start_radio=1, index=...) trên YouTube để tránh lỗi 403 / tải vô hạn.
    - Bảo toàn URL playlist thực thụ (vd: youtube.com/playlist?list=PL...).
    """
    if not raw_url:
        return ""
    
    # 1. Trích xuất URL từ chuỗi (hỗ trợ trường hợp paste cả đoạn text chia sẻ)
    url_match = re.search(r'https?://[^\s"\'<>`]+', raw_url)
    if url_match:
        url = url_match.group(0)
    else:
        url = raw_url.strip().strip('"\'`<>')
        
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return url
            
        netloc = parsed.netloc.lower()
        path = parsed.path
        query_dict = parse_qs(parsed.query, keep_blank_values=False)
        
        # Danh sách tracking parameters chung
        common_tracking = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "fbclid", "igsh", "si", "feature", "pp", "ab_channel", "attr_tag",
            "ref", "ref_src", "is_from_webapp", "sender_device", "mibextid"
        }
        
        # Xóa các tracking query parameters chung
        for key in list(query_dict.keys()):
            if key.lower() in common_tracking:
                query_dict.pop(key, None)
                
        # Xử lý theo từng nền tảng
        is_youtube = any(yt in netloc for yt in ["youtube.com", "youtu.be"]) or (platform and platform.lower() in ["ytb", "ytb-music"])
        
        if is_youtube:
            # Nếu là link video đơn lẻ (watch?v=... hoặc youtu.be/...)
            if path in ["/watch", "/watch_popup"] or "youtu.be" in netloc or "v" in query_dict:
                # Xử lý list: nếu là Radio Mix (bắt đầu bằng RD) hoặc các list đặc biệt -> xóa để tải đúng video đó
                if "list" in query_dict:
                    list_val = query_dict["list"][0] if query_dict["list"] else ""
                    if list_val.startswith("RD") or list_val in ["LL", "WL"]:
                        query_dict.pop("list", None)
                query_dict.pop("start_radio", None)
                query_dict.pop("index", None)
                
        elif "tiktok.com" in netloc or platform == "tiktok":
            tiktok_tracking = {"is_copy_url", "ug_source", "enter_from", "enter_method", "share_app_id", "share_item_id", "share_link_id", "source"}
            for key in tiktok_tracking:
                query_dict.pop(key, None)
                
        elif "bilibili.com" in netloc or "b23.tv" in netloc or (platform and platform.lower() in ["bilibili", "bili", "bilili"]):
            bili_tracking = {"spm_id_from", "from_source", "from", "seid", "share_source", "share_medium", "share_plat", "share_session_id", "share_tag", "unique_k", "vd_source"}
            for key in bili_tracking:
                query_dict.pop(key, None)

        elif "spotify.com" in netloc or (platform and platform.lower() in ["spot", "spotify"]):
            query_dict.pop("context", None)

        elif "twitter.com" in netloc or "x.com" in netloc or (platform and platform.lower() in ["twitter", "x"]):
            query_dict.pop("s", None)
            query_dict.pop("t", None)

        # Tái tạo lại query string
        new_query = urlencode(query_dict, doseq=True)
        cleaned = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        return cleaned.rstrip("?")
    except Exception:
        return url

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

