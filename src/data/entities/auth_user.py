from dataclasses import dataclass


@dataclass
class AuthUser:
    """Usuario autenticado (Supabase Auth)."""

    id: str
    email: str | None = None

    @classmethod
    def from_auth(cls, user) -> "AuthUser | None":
        if user is None:
            return None
        return cls(id=str(user.id), email=getattr(user, "email", None))
