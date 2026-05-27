import flet as ft

class StatusBanner(ft.Container):
    def __init__(self):
        self._status_icon = ft.Icon(ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY, size=18)
        self._status_text = ft.Text("", size=13, expand=True)

        super().__init__(
            content=ft.Row(
                spacing=8,
                controls=[self._status_icon, self._status_text],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(8),
            padding=ft.Padding(left=12, top=10, right=12, bottom=10),
            visible=False,
        )

    def show(self, message: str, is_error: bool = False, is_success: bool = False) -> None:
        self._status_text.value = message
        if is_error:
            self._status_icon.name = ft.Icons.ERROR_OUTLINE
            self._status_icon.color = ft.Colors.ERROR
            self._status_banner_bgcolor = ft.Colors.ERROR_CONTAINER
            self.bgcolor = ft.Colors.ERROR_CONTAINER
            self._status_text.color = ft.Colors.ON_ERROR_CONTAINER
            self.border = ft.Border.all(1, ft.Colors.ERROR)
        elif is_success:
            self._status_icon.name = ft.Icons.CHECK_CIRCLE_OUTLINE
            self._status_icon.color = ft.Colors.GREEN_700
            self.bgcolor = ft.Colors.GREEN_100
            self._status_text.color = ft.Colors.GREEN_900
            self.border = ft.Border.all(1, ft.Colors.GREEN_700)
        else:
            self._status_icon.name = ft.Icons.INFO_OUTLINED
            self._status_icon.color = ft.Colors.PRIMARY
            self.bgcolor = ft.Colors.SURFACE_CONTAINER_LOW
            self._status_text.color = ft.Colors.ON_SURFACE
            self.border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        self.visible = bool(message)
        if getattr(self, "_page", None):
            self.update()

    def hide(self) -> None:
        self.visible = False
        if getattr(self, "_page", None):
            self.update()
