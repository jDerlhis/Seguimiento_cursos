import flet as ft

from infra.auth.mfa_coordinator import MfaRequest, MfaStatus, mfa_coordinator


def _is_valid_mfa_code(code: str) -> bool:
    """Acepta codigos de 6 caracteres alfanumericos (digitos, letras o mezcla).
    Ejemplos validos: 123456, 94CTX2, ABCDEF, A1B2C3
    """
    if len(code) != 6:
        return False
    return bool(__import__("re").match(r"^[A-Z0-9]{6}$", code.upper()))


class MfaDialog:
    """Modal MFA con cuenta regresiva, expiracion y reenvio de codigo.
    Acepta codigos alfanumericos de 6 caracteres (ej: 94CTX2, 123456).
    """

    def __init__(self, page: ft.Page) -> None:
        self._page = page

        self._code_field = ft.TextField(
            label="Codigo de verificacion",
            hint_text="6 caracteres del correo (ej: 94CTX2)",
            autofocus=True,
            max_length=6,
            # Forzar mayusculas para evitar confusion entre O/0, l/1
            capitalization=ft.TextCapitalization.CHARACTERS,
            on_submit=self._on_submit,
        )
        self._message = ft.Text(size=14, color=ft.Colors.ON_SURFACE_VARIANT)
        self._countdown = ft.Text(
            size=13,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self._error = ft.Text(size=13, color=ft.Colors.ERROR, visible=False)
        self._info = ft.Text(size=13, color=ft.Colors.PRIMARY, visible=False)

        self._resend_button = ft.TextButton(
            "Reenviar codigo",
            icon=ft.Icons.REFRESH,
            on_click=self._on_resend,
        )

        self._dialog = ft.AlertDialog(
            modal=True,
            barrier_color=ft.Colors.with_opacity(0.45, ft.Colors.SCRIM),
            title=ft.Text("Autenticacion de doble factor"),
            content=ft.Column(
                tight=True,
                spacing=12,
                width=380,
                controls=[
                    self._message,
                    self._countdown,
                    self._code_field,
                    self._error,
                    self._info,
                    self._resend_button,
                ],
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self._on_cancel),
                ft.FilledButton("Validar acceso", on_click=self._on_submit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def open(self, request: MfaRequest) -> None:
        self._message.value = request.message
        self._code_field.value = ""
        self._error.visible = False
        self._info.visible = False
        self._resend_button.disabled = False
        self._apply_status(mfa_coordinator.get_status())

        if self._dialog not in self._page.overlay:
            self._page.overlay.append(self._dialog)
        self._dialog.open = True
        self._page.update()

    def close(self) -> None:
        self._dialog.open = False
        if self._dialog in self._page.overlay:
            self._page.overlay.remove(self._dialog)
        self._page.update()

    def show_error(self, message: str) -> None:
        if not self._dialog.open:
            if self._dialog not in self._page.overlay:
                self._page.overlay.append(self._dialog)
            self._dialog.open = True
        self._error.value = message
        self._error.visible = True
        self._info.visible = False
        self._code_field.value = ""
        self._resend_button.disabled = False
        self._page.update()

    def _apply_status(self, status: MfaStatus) -> None:
        if status.countdown_text:
            if status.expired:
                self._countdown.value = f"Codigo: {status.countdown_text}"
                self._countdown.color = ft.Colors.ERROR
                self._error.value = (
                    "Codigo expirado. Pulsa «Reenviar codigo» para recibir uno nuevo."
                )
                self._error.visible = True
                self._resend_button.disabled = False
            else:
                self._countdown.value = f"Expira en: {status.countdown_text}"
                self._countdown.color = ft.Colors.ON_SURFACE_VARIANT
        else:
            self._countdown.value = "Esperando codigo en tu correo..."
            self._countdown.color = ft.Colors.ON_SURFACE_VARIANT

    def _on_resend(self, e: ft.ControlEvent) -> None:
        if not mfa_coordinator.is_session_active():
            self.show_error("No hay sesion de login activa.")
            return

        self._error.visible = False
        self._info.value = "Reenviando codigo al correo..."
        self._info.visible = True
        self._code_field.value = ""
        self._resend_button.disabled = True
        self._page.update()

        mfa_coordinator.request_resend()

    def _on_cancel(self, e: ft.ControlEvent) -> None:
        if not mfa_coordinator.is_session_active():
            self.close()
            return
        mfa_coordinator.cancel()
        self.close()

    def _on_submit(self, e: ft.ControlEvent) -> None:
        if not mfa_coordinator.is_session_active():
            self.show_error("No hay sesion de login activa.")
            return

        code = (self._code_field.value or "").strip().upper()

        # Validacion: 6 caracteres alfanumericos (letras A-Z y/o digitos 0-9)
        if not _is_valid_mfa_code(code):
            self.show_error(
                "Ingresa un codigo valido de 6 caracteres (letras y/o numeros). "
                "Ejemplo: 94CTX2 o 123456"
            )
            return

        self._error.visible = False
        self._info.value = "Validando codigo..."
        self._info.visible = True
        self._page.update()
        mfa_coordinator.submit_code(code)


def register_mfa_ui(page: ft.Page) -> MfaDialog:
    dialog = MfaDialog(page)

    def _run_async(coro_fn) -> None:
        page.run_task(coro_fn)

    def show_on_main_thread(request: MfaRequest) -> None:
        async def task() -> None:
            dialog.open(request)

        _run_async(task)

    def show_error_on_main_thread(message: str) -> None:
        async def task() -> None:
            dialog.show_error(message)

        _run_async(task)

    def update_status_on_main_thread(status: MfaStatus) -> None:
        async def task() -> None:
            if not dialog._dialog.open:
                return
            dialog._apply_status(status)
            if not status.expired:
                dialog._error.visible = False
            if mfa_coordinator.is_session_active():
                dialog._resend_button.disabled = False
            dialog._info.visible = False
            page.update()

        _run_async(task)

    def close_on_main_thread() -> None:
        async def task() -> None:
            if dialog._dialog.open:
                dialog.close()

        _run_async(task)

    mfa_coordinator.set_ui_handler(show_on_main_thread)
    mfa_coordinator.set_error_handler(show_error_on_main_thread)
    mfa_coordinator.set_status_handler(update_status_on_main_thread)
    mfa_coordinator.set_close_handler(close_on_main_thread)
    return dialog