from dataclasses import dataclass


@dataclass(frozen=True)
class EmailCredentials:
    email: str
    password: str


class AuthError(Exception):
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return self.message
