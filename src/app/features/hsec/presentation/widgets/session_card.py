import flet as ft

_STATE_COLORS = {
    "checking": ft.Colors.OUTLINE,
    "disconnected": ft.Colors.ERROR,
    "connecting": ft.Colors.TERTIARY,
    "mfa_required": ft.Colors.AMBER_700,
    "connected": ft.Colors.GREEN,
    "error": ft.Colors.ERROR,
}


class SessionCard(ft.Container):
    """Tarjeta de estado de la sesión HSEC activa."""

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
        self._dot.bgcolor = _STATE_COLORS.get(state, ft.Colors.OUTLINE)
        self._title.value = title
        self._subtitle.value = subtitle
        self._subtitle.visible = bool(subtitle)
