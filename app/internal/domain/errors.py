class AuthError(Exception):
    def __init__(self, message: str = "Authentication error"):
        self.message = message
        super().__init__(self.message)

class GoogleAuthError(AuthError):
    pass

class TokenError(AuthError):
    pass

class UserNotFoundError(Exception):
    def __init__(self, message: str = "User not found"):
        self.message = message
        super().__init__(self.message)

class SongNotFoundError(Exception):
    def __init__(self, message: str = "Song not found"):
        self.message = message
        super().__init__(self.message)
