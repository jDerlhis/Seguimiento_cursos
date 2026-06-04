import flet as ft

from app.features.sign_in.domain import auth_service
from app.features.sign_in.presentation import build_sign_in_view
from app.router.app_shell import build_shell


def navigate_to_sign_in(page: ft.Page) -> None:
    page.controls.clear()
    page.add(build_sign_in_view(page, on_authenticated=lambda: navigate_to_shell(page)))
    page.update()


def navigate_to_shell(page: ft.Page) -> None:
    page.controls.clear()
    page.add(build_shell(page, on_logout=lambda: navigate_to_sign_in(page)))
    page.update()


def build_root(page: ft.Page) -> ft.Control:
    if auth_service.is_logged_in():
        return build_shell(page, on_logout=lambda: navigate_to_sign_in(page))
    return build_sign_in_view(page, on_authenticated=lambda: navigate_to_shell(page))
