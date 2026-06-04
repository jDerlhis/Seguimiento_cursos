from data.entities.auth_user import AuthUser
from app.common.modules.auth.types import AuthError, EmailCredentials
from app.features.sign_in.domain import auth_repository, tenant_members_repository


def login(email: str, password: str) -> AuthUser:
    user = auth_repository.sign_in(EmailCredentials(email=email, password=password))
    tenant_members_repository.ensure_desktop_tenant_membership(user.id)
    return user


def register(email: str, password: str, password_confirm: str) -> AuthUser:
    if password != password_confirm:
        raise AuthError("Las contraseñas no coinciden.")

    user = auth_repository.sign_up(EmailCredentials(email=email, password=password))
    tenant_members_repository.ensure_desktop_tenant_membership(user.id)
    return user


def logout() -> None:
    auth_repository.sign_out_user()


def current_user() -> AuthUser | None:
    return auth_repository.get_current_user()


def is_logged_in() -> bool:
    return auth_repository.is_authenticated()
