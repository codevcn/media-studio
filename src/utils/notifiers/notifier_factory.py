from .base_notifier import BaseNotifier
from .telegram_notifier import TelegramNotifier

class NotifierFactory:
    @staticmethod
    def get_notifier(notice_type: str) -> BaseNotifier:
        """
        Factory method to get the appropriate notifier based on type.
        """
        if not notice_type:
            return None
            
        notice_type = notice_type.lower()
        if notice_type == "telegram":
            return TelegramNotifier()
        # You can add more notifiers here in the future
        # elif notice_type == "discord":
        #     return DiscordNotifier()
        
        print(f">>> Warn: Loại thông báo '{notice_type}' chưa được hỗ trợ.")
        return None
