class BotError(Exception):
    def __init__(self, message: str, send_message: str | None = None):
        self.message = message
        self.send_message = send_message or message
        super().__init__(self.message)


class PermissionError(BotError):
    pass


class MemberNotFoundError(BotError):
    pass