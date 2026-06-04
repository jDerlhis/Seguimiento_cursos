import threading

import flet as ft

from app.common.modules.hsec.login import login_hsec
from app.common.modules.hsec.persistence import load_active_session
from infra.supabase.tenant import get_tenant_id
from shared.logger import get_logger

logger = get_logger(__name__)

_STATE_DOT_COLORS = {
    "checking": ft.Colors.OUTLINE,
    "disconnected": ft.Colors.ERROR,
    "connecting": ft.Colors.TERTIARY,
    "mfa_required": ft.Colors.AMBER_700,
    "connected": ft.Colors.GREEN,
    "error": ft.Colors.ERROR,
}


class _SessionCard(ft.Container):
    """Tarjeta de estado de sesión activa."""

    def __init__(self):
        self._dot = ft.Container(
            width=10, height=10, border_radius=5, bgcolor=ft.Colors.OUTLINE
        )
        self._title = ft.Text(
            "Verificando sesión...", size=14, weight=ft.FontWeight.W_600
        )
        self._subtitle = ft.Text(
            "", size=12, color=ft.Colors.ON_SURFACE_VARIANT, visible=False
        )

        super().__init__(
            padding=ft.Padding.symmetric(horizontal=20, vertical=18),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Row(
                        [self._dot, self._title],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=self._subtitle,
                        padding=ft.Padding(left=20, top=0, right=0, bottom=0),
                    ),
                ],
            ),
        )

    def set(self, state: str, title: str, subtitle: str = "") -> None:
        self._dot.bgcolor = _STATE_DOT_COLORS.get(state, ft.Colors.OUTLINE)
        self._title.value = title
        self._subtitle.value = subtitle
        self._subtitle.visible = bool(subtitle)


class HsecView(ft.Column):
    def __init__(self, page: ft.Page):
        self._page = page
        self._tenant_id: str | None = None

        self._session_card = _SessionCard()

        # Banner de mensajes
        self._banner_icon = ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=16)
        self._banner_text = ft.Text("", size=13, expand=True)
        self._banner = ft.Container(
            visible=False,
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            border_radius=10,
            content=ft.Row(
                [self._banner_icon, self._banner_text],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # Campo MFA
        self._mfa_field = ft.TextField(
            label="Código MFA",
            prefix_icon=ft.Icons.SECURITY_ROUNDED,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            width=220,
            visible=False,
        )

        # Indicador de progreso en ejecución
        self._progress_text = ft.Text(
            "", size=13, color=ft.Colors.ON_SURFACE_VARIANT
        )
        self._progress_row = ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2.5),
                self._progress_text,
            ],
            spacing=10,
            visible=False,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Botones de acción
        self._connect_btn = ft.FilledButton(
            "Conectar",
            icon=ft.Icons.LINK_ROUNDED,
            on_click=self._on_connect,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            visible=False,
        )
        self._verify_btn = ft.FilledButton(
            "Verificar código",
            icon=ft.Icons.VERIFIED_USER_ROUNDED,
            on_click=self._on_connect,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            visible=False,
        )
        self._reconnect_btn = ft.OutlinedButton(
            "Reconectar",
            icon=ft.Icons.REFRESH_ROUNDED,
            on_click=self._on_connect,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            visible=False,
        )

        super().__init__(
            spacing=16,
            controls=[
                self._session_card,
                self._banner,
                self._mfa_field,
                self._progress_row,
                ft.Row(
                    spacing=10,
                    controls=[self._connect_btn, self._verify_btn, self._reconnect_btn],
                ),
            ],
        )

        threading.Thread(target=self._load_session_status, daemon=True).start()

    # ─── Estado visual ────────────────────────────────────────────────────────

    def _apply_state(
        self,
        state: str,
        *,
        session_id: str | None = None,
        message: str = "",
    ) -> None:
        if state == "checking":
            self._session_card.set("checking", "Verificando sesión...")
        elif state == "disconnected":
            self._session_card.set(
                "disconnected", "Sin sesión activa",
                "Conecta tu cuenta para acceder al portal HSEC"
            )
        elif state == "connecting":
            self._session_card.set(
                "connecting", "Conectando al portal...",
                "Esto puede tardar unos segundos"
            )
        elif state == "mfa_required":
            self._session_card.set(
                "mfa_required", "Verificación MFA requerida",
                "Ingresa el código enviado a tu dispositivo"
            )
        elif state == "connected":
            sid = f"Sesión: {session_id[:12]}..." if session_id else "Sesión restaurada"
            self._session_card.set("connected", "Conectado", sid)
        elif state == "error":
            self._session_card.set(
                "error", "Error de conexión",
                "Revisa el error y vuelve a intentarlo"
            )

        # Banner
        if message:
            is_error = state == "error"
            self._show_banner(message, is_error=is_error)
        elif state not in ("mfa_required",):
            self._banner.visible = False

        # Progreso
        self._progress_row.visible = state == "connecting"
        if state == "connecting":
            self._progress_text.value = "Abriendo navegador..."

        # Campo MFA
        self._mfa_field.visible = state == "mfa_required"

        # Botones
        is_busy = state == "connecting"
        self._connect_btn.visible = state in ("disconnected", "error")
        self._connect_btn.disabled = is_busy
        self._verify_btn.visible = state == "mfa_required"
        self._verify_btn.disabled = is_busy
        self._reconnect_btn.visible = state == "connected"
        self._reconnect_btn.disabled = is_busy

    def _show_banner(self, message: str, *, is_error: bool) -> None:
        if is_error:
            self._banner.bgcolor = ft.Colors.ERROR_CONTAINER
            self._banner_text.color = ft.Colors.ON_ERROR_CONTAINER
            self._banner_icon.color = ft.Colors.ON_ERROR_CONTAINER
            self._banner_icon.name = ft.Icons.ERROR_OUTLINE_ROUNDED
        else:
            self._banner.bgcolor = ft.Colors.PRIMARY_CONTAINER
            self._banner_text.color = ft.Colors.ON_PRIMARY_CONTAINER
            self._banner_icon.color = ft.Colors.ON_PRIMARY_CONTAINER
            self._banner_icon.name = ft.Icons.INFO_OUTLINE_ROUNDED
        self._banner_text.value = message
        self._banner.visible = True

    # ─── Carga inicial ────────────────────────────────────────────────────────

    def _load_session_status(self) -> None:
        try:
            self._tenant_id = get_tenant_id()
            session = load_active_session(self._tenant_id)
            if session:
                self._apply_state("connected", session_id=session["session_id"])
            else:
                self._apply_state("disconnected")
        except Exception as ex:
            logger.warning("Error al verificar sesión HSEC: %s", ex)
            self._apply_state("disconnected")
        finally:
            self._page.update()

    # ─── Acciones ─────────────────────────────────────────────────────────────

    def _on_connect(self, _e) -> None:
        self._apply_state("connecting")
        self._page.update()

        def _run() -> None:
            try:
                if self._tenant_id is None:
                    self._tenant_id = get_tenant_id()
                mfa_code = (self._mfa_field.value or "").strip() if self._mfa_field.visible else ""
                result = login_hsec(self._tenant_id, mfa_code=mfa_code)

                if result.mfa_required and not mfa_code:
                    self._apply_state("mfa_required", message=result.message)
                elif result.success:
                    self._apply_state("connected", session_id=result.session_id)
                else:
                    self._apply_state("error", message=result.message)
            except Exception as ex:
                logger.exception("Login HSEC")
                self._apply_state("error", message=str(ex) or "Error inesperado al conectar.")
            finally:
                self._page.update()

        threading.Thread(target=_run, daemon=True).start()


def build_hsec_view(page: ft.Page) -> HsecView:
    return HsecView(page)
