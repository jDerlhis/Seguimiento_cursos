import flet as ft

from app.common.modules.hsec.login import login_hsec
from infra.supabase.tenant import get_tenant_id
from shared.logger import get_logger

logger = get_logger(__name__)


class _StatusBanner(ft.Container):
    def __init__(self):
        self._text = ft.Text("", size=13)
        super().__init__(visible=False, padding=12, border_radius=8, content=self._text)

    def show_info(self, message: str) -> None:
        self.bgcolor = ft.Colors.PRIMARY_CONTAINER
        self._text.value = message
        self._text.color = ft.Colors.ON_PRIMARY_CONTAINER
        self.visible = True

    def show_error(self, message: str) -> None:
        self.bgcolor = ft.Colors.ERROR_CONTAINER
        self._text.value = message
        self._text.color = ft.Colors.ON_ERROR_CONTAINER
        self.visible = True

    def show_success(self, message: str) -> None:
        self.bgcolor = ft.Colors.TERTIARY_CONTAINER
        self._text.value = message
        self._text.color = ft.Colors.ON_TERTIARY_CONTAINER
        self.visible = True


class HsecView(ft.Column):
    def __init__(self, page: ft.Page):
        self._page = page
        self._banner = _StatusBanner()
        self._mfa = ft.TextField(label="Código MFA (si aplica)", visible=False)
        self._login_btn = ft.FilledButton(
            "Iniciar sesión HSEC",
            icon=ft.Icons.LOGIN,
            on_click=self._on_login,
        )
        super().__init__(
            expand=True,
            spacing=16,
            controls=[
                ft.Text("Conexión HSEC Web", size=20, weight=ft.FontWeight.W_600),
                ft.Text(
                    "La sesión del navegador se guarda en la tabla hsec_sessions (Supabase).",
                    size=13,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                self._banner,
                self._mfa,
                self._login_btn,
            ],
        )

    def _on_login(self, _e) -> None:
        self._banner.show_info("Abriendo navegador...")
        self._login_btn.disabled = True
        self._page.update()

        try:
            tenant_id = get_tenant_id()
            mfa_code = (self._mfa.value or "").strip()
            result = login_hsec(tenant_id, mfa_code=mfa_code)

            if result.mfa_required and not mfa_code:
                self._mfa.visible = True
                self._banner.show_error(result.message)
                return

            if result.success:
                self._banner.show_success(result.message)
            else:
                self._banner.show_error(result.message)
        except Exception as ex:
            logger.exception("Login HSEC")
            self._banner.show_error(str(ex))
        finally:
            self._login_btn.disabled = False
            self._page.update()
