import os
import requests
from dotenv import load_dotenv

from configs.paths import ROOT_FOLDER_PATH
from .base_notifier import BaseNotifier

# Load .env file
env_path = os.path.join(ROOT_FOLDER_PATH, ".env")
load_dotenv(dotenv_path=env_path)

class TelegramNotifier(BaseNotifier):
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def notify(self, message: str) -> bool:
        if not self.bot_token or not self.chat_id:
            print(">>> Warn: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(">>> Đã gửi thông báo Telegram thành công.")
                return True
            else:
                print(f">>> Warn: Gửi Telegram thất bại. HTTP {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f">>> Warn: Lỗi khi gửi Telegram: {e}")
            return False
