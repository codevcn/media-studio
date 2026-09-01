"""
Media Studio CLI (mda) Version & Metadata Configuration
"""

__version__ = "0.1.0"
__app_name__ = "Media Studio CLI"
__cli_name__ = "mda"
__author__ = "Media Studio Team"
__description__ = (
    "All-in-one multimedia processing CLI tool: video editing, "
    "watermark removal, audio extraction, image manipulation, "
    "multi-platform downloader, and OCR."
)


def get_version_info() -> str:
    """Trả về chuỗi thông tin phiên bản và mô tả ngắn bằng tiếng Anh"""
    return f"{__app_name__} ({__cli_name__}) v{__version__}\n{__description__}"


def get_version_short() -> str:
    """Trả về chuỗi phiên bản ngắn dạng v0.1.0"""
    return f"v{__version__}"
