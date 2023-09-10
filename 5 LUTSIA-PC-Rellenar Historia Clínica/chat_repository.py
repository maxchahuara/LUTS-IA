
class ChatRepository:
    def __init__(self):
        # Using a list to store chat messages. In a real-world scenario, this could be a database.
        self.chat_content = []

    def add_message(self, message):
        self.chat_content.append(message)

    def get_chat_content(self):
        return self.chat_content

    def clear_chat(self):
        self.chat_content.clear()

chat_repo = ChatRepository()  # Singleton instance
