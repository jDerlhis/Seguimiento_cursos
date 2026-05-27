import threading

import flet as ft

from app.features.hsec.mfa_dialog import register_mfa_ui
from infra.auth.session_store import clear_session, has_saved_session
from infra.initializer import check_session_status
from infra.auth.mfa_email_fetcher import is_mfa_email_configured
from infra.config.settings import (
    HSEC_DASHBOARD_URL,
    HSEC_SESSION_FILE,
    HSEC_USERNAME,
    MFA_IMAP_USER,
    PYFLOW_WEBHOOK_URL,
)
from infra.scraping.hsec_scraper import login_hsec


class HsecView(ft.Column):
    def __init__(self, page: ft.Page):
        self._page = page
        self._mfa_dialog = register_mfa_ui(page)

        self._status = ft.Text(size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self._session_chip = ft.Chip(
            label="Sin sesión guardada",
            leading=ft.Icon(ft.Icons.LINK_OFF),
        )
        self._progress = ft.ProgressRing(visible=False, width=20, height=20)

        super().__init__(
            expand=True,
            spacing=16,
            controls=[
                ft.Text(
                    "HSEC Web — Glencore Antapaccay",
                    size=18,
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(
                    HSEC_DASHBOARD_URL,
                    size=12,
                    color=ft.Colors.OUTLINE,
                    selectable=True,
                ),
                ft.Row(
                    spacing=12,
                    controls=[
                        self._session_chip,
                        ft.Text(
                            f"Webhook: {'configurado' if PYFLOW_WEBHOOK_URL else 'no configurado'}",
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(
                            (
                                f"MFA correo: {MFA_IMAP_USER} (auto)"
                                if is_mfa_email_configured()
                                else "MFA correo: no configurado"
                            ),
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                ),
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.FilledButton(
                            "Iniciar sesión",
                            icon=ft.Icons.LOGIN,
                            on_click=self._on_login_click,
                        ),
                        ft.OutlinedButton(
                            "Cerrar sesión",
                            icon=ft.Icons.LOGOUT,
                            on_click=self._on_logout_click,
                        ),
                        self._progress,
                    ],
                ),
                self._status,
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("Flujo implementado:", weight=ft.FontWeight.W_500),
                            ft.Text(
                                "1. Abre el dashboard de HSEC con Playwright.\n"
                                "2. Si hay sesión guardada, la reutiliza.\n"
                                "3. Si pide credenciales, usa HSEC_USERNAME / HSEC_PASSWORD del .env.\n"
                                "4. MFA: lee el código del buzón IMAP y/o modal manual (cuenta regresiva, Reenviar).\n"
                                f"5. Tras el login, guarda la sesión en:\n   {HSEC_SESSION_FILE}\n"
                                "6. Webhooks: hsec.mfa.required, hsec.mfa.expired, hsec.mfa.resent, hsec.auth.success.",
                                size=13,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                    ),
                ),
            ],
        )
        self._refresh_session_chip()

    def _refresh_session_chip(self) -> None:
        status = check_session_status()
        if not status["exists"]:
            self._session_chip.label = "Sin sesión guardada"
            self._session_chip.leading = ft.Icon(ft.Icons.LINK_OFF)
        elif status["expired"]:
            user_lbl = f" ({status['username']})" if status['username'] else ""
            self._session_chip.label = f"Sesión expirada{user_lbl}"
            self._session_chip.leading = ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.ERROR)
        else:
            user_lbl = f": {status['username']}" if status['username'] else ""
            self._session_chip.label = f"Sesión activa{user_lbl}"
            self._session_chip.leading = ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINED, color=ft.Colors.GREEN)

    def _set_loading(self, loading: bool) -> None:
        self._progress.visible = loading
        self._page.update()

    def _on_logout_click(self, e: ft.ControlEvent) -> None:
        clear_session()
        self._refresh_session_chip()
        self._status.value = "Sesión local eliminada. El próximo inicio pedirá login completo."
        self._page.update()

    def _on_login_click(self, e: ft.ControlEvent) -> None:
        if not HSEC_USERNAME:
            self._status.value = (
                "Configura HSEC_USERNAME y HSEC_PASSWORD en un archivo .env en la raíz del proyecto."
            )
            self._page.update()
            return

        self._status.value = "Conectando con HSEC Web..."
        self._set_loading(True)

        def task() -> None:
            try:
                result = login_hsec()
                parts = [result.message]
                if result.used_saved_session:
                    parts.append("(sesión reutilizada)")
                if result.mfa_required:
                    parts.append("(MFA completado)")
                self._status.value = " ".join(parts)
                self._refresh_session_chip()
            except Exception as ex:
                self._status.value = f"Error al iniciar sesión: {ex}"
            finally:
                self._set_loading(False)
                self._page.update()

        threading.Thread(target=task, daemon=True).start()
