from abc import ABC, abstractmethod

class BaseNotifier(ABC):
    """
    Abstract base class for all notifiers.
    """
    @abstractmethod
    def notify(self, message: str) -> bool:
        """
        Send a notification with the given message.
        :param message: The text message to send.
        :return: True if successful, False otherwise.
        """
        pass
