# chat_history.py

from datetime import datetime

class ChatHistory:
    def __init__(self):
        self.messages = []          # 전체 메시지 저장
        self.customer_messages = [] # 고객 메시지만 저장

    def add_message(self, sender: str, text: str):
        msg = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "sender": sender,
            "text": text
        }

        self.messages.append(msg)

        if sender == "customer":
            self.customer_messages.append(msg)

    def get_customer_messages(self):
        return self.customer_messages

    def clear(self):
        self.messages = []
        self.customer_messages = []
