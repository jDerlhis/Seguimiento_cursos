from typing import Callable

import flet as ft

from app.common.modules.auth.types import AuthError
from app.features.sign_in.domain import auth_service
from app.features.sign_in.presentation.widgets.auth_card import AuthCard
from shared import theme


class SignInView(ft.Container):
    """Pantalla de inicio de sesión y registro (email/contraseña)."""

    def __init__(self, page: ft.Page, on_authenticated: Callable[[], None]):
        self._page = page
        self._on_authenticated = on_authenticated
        self._mode = "login"

        self._error_text_inner = ft.Text(
            "", size=13, color=ft.Colors.ON_ERROR_CONTAINER, expand=True
        )
        self._error_banner = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, size=16, color=ft.Colors.ON_ERROR_CONTAINER),
                    self._error_text_inner,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            border_radius=10,
            bgcolor=ft.Colors.ERROR_CONTAINER,
            visible=False,
        )

        self._success_text_inner = ft.Text(
            "", size=13, color=ft.Colors.ON_TERTIARY_CONTAINER, expand=True
        )
        self._success_banner = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                        size=16,
                        color=ft.Colors.ON_TERTIARY_CONTAINER,
                    ),
                    self._success_text_inner,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            border_radius=10,
            bgcolor=ft.Colors.TERTIARY_CONTAINER,
            visible=False,
        )

        self._loading = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2.5)

        self._email = ft.TextField(
            label="Correo electrónico",
            prefix_icon=ft.Icons.ALTERNATE_EMAIL_ROUNDED,
            keyboard_type=ft.KeyboardType.EMAIL,
            autocorrect=False,
            autofocus=True,
            border_radius=12,
        )
        self._password = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
            password=True,
            can_reveal_password=True,
            border_radius=12,
        )
        self._password_confirm = ft.TextField(
            label="Confirmar contraseña",
            prefix_icon=ft.Icons.LOCK_RESET_ROUNDED,
            password=True,
            can_reveal_password=True,
            border_radius=12,
            visible=False,
        )

        self._submit_btn = ft.FilledButton(
            "Iniciar sesión",
            icon=ft.Icons.LOGIN_ROUNDED,
            on_click=self._on_submit,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            expand=True,
        )

        self._mode_switch = ft.SegmentedButton(
            selected={"login"},
            on_change=self._on_mode_change,
            expand_loose=True,
            segments=[
                ft.Segment(value="login", label=ft.Text("Iniciar sesión")),
                ft.Segment(value="register", label=ft.Text("Registrarse")),
            ],
        )

        form = ft.Column(
            spacing=14,
            controls=[
                ft.Container(
                    content=self._mode_switch,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Container(height=2),
                self._email,
                self._password,
                self._password_confirm,
                self._error_banner,
                self._success_banner,
                ft.Container(height=4),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._loading,
                        self._submit_btn,
                    ],
                ),
            ],
        )

        super().__init__(
            expand=True,
            bgcolor=theme.CONTENT_BG,
            alignment=ft.Alignment(0, 0),
            content=AuthCard(
                title="Pyflow",
                subtitle="Seguimiento de cursos HSEC",
                form=form,
                footer=ft.Text(
                    "Usa el correo y contraseña de tu cuenta Supabase.",
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                ),
            ),
        )

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        is_register = mode == "register"
        self._password_confirm.visible = is_register
        self._submit_btn.text = "Crear cuenta" if is_register else "Iniciar sesión"
        self._submit_btn.icon = ft.Icons.PERSON_ADD_ROUNDED if is_register else ft.Icons.LOGIN_ROUNDED
        self._clear_messages()

    def _on_mode_change(self, e: ft.ControlEvent) -> None:
        selected = list(e.control.selected)[0] if e.control.selected else "login"
        self._set_mode(selected)
        self.update()

    def _clear_messages(self) -> None:
        self._error_text_inner.value = ""
        self._error_banner.visible = False
        self._success_text_inner.value = ""
        self._success_banner.visible = False

    def _show_error(self, message: str) -> None:
        self._success_banner.visible = False
        self._error_text_inner.value = message
        self._error_banner.visible = True

    def _show_success(self, message: str) -> None:
        self._error_banner.visible = False
        self._success_text_inner.value = message
        self._success_banner.visible = True

    def _set_loading(self, loading: bool) -> None:
        self._loading.visible = loading
        self._submit_btn.disabled = loading
        self._email.disabled = loading
        self._password.disabled = loading
        self._password_confirm.disabled = loading

    def _on_submit(self, _e) -> None:
        self._clear_messages()
        email = (self._email.value or "").strip()
        password = self._password.value or ""

        if not email or not password:
            self._show_error("Completa correo y contraseña.")
            self.update()
            return

        if self._mode == "register" and password != (self._password_confirm.value or ""):
            self._show_error("Las contraseñas no coinciden.")
            self.update()
            return

        self._set_loading(True)
        self.update()

        try:
            if self._mode == "login":
                auth_service.login(email, password)
            else:
                auth_service.register(
                    email,
                    password,
                    self._password_confirm.value or "",
                )
            self._on_authenticated()
        except AuthError as ex:
            if ex.code == "email_confirmation_required":
                self._show_success(str(ex))
            else:
                self._show_error(str(ex))
        except Exception as ex:
            self._show_error(str(ex) or "Error inesperado.")
        finally:
            self._set_loading(False)
            self.update()


def build_sign_in_view(page: ft.Page, on_authenticated: Callable[[], None]) -> SignInView:
    return SignInView(page, on_authenticated)
