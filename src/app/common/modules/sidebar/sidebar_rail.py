import flet as ft

import shared.theme as theme
from app.common.modules.sidebar.navigation import NAV_SECTIONS, NavSection



class SidebarRail(ft.Container):
    def __init__(
        self,
        on_section_change,
        active_section_id: str,
        on_toggle_menu=None,
        on_logout=None,
    ):
        self._on_section_change = on_section_change
        self._active_section_id = active_section_id
        self._on_toggle_menu = on_toggle_menu
        self._on_logout = on_logout
        self._buttons: dict[str, ft.IconButton] = {}
        self._toggle_btn: ft.IconButton | None = None

        super().__init__(
            width=theme.RAIL_WIDTH,
            bgcolor=theme.RAIL_BG,
            padding=ft.Padding.symmetric(vertical=12, horizontal=8),
            content=self._build_content(),
        )

    def _icon(self, name: str) -> str:
        return getattr(ft.Icons, name.upper())

    def _build_icon_button(self, section: NavSection) -> ft.IconButton:
        selected = section.id == self._active_section_id

        def on_click(e: ft.ControlEvent) -> None:
            self._on_section_change(section.id)

        btn = ft.IconButton(
            icon=self._icon(section.icon if not selected else section.selected_icon),
            selected=selected,
            tooltip=section.label,
            icon_color=theme.RAIL_ICON_SELECTED if selected else theme.RAIL_ICON_DEFAULT,
            bgcolor=theme.RAIL_BTN_SELECTED_BG if selected else None,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            on_click=on_click,
        )
        self._buttons[section.id] = btn
        return btn

    def _build_content(self) -> ft.Control:
        return ft.Column(
            controls=[
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    height=40,
                    content=ft.Icon(ft.Icons.BOLT, color=ft.Colors.PRIMARY, size=28),
                ),
                ft.Divider(height=8, color=ft.Colors.OUTLINE_VARIANT),
                *[
                    ft.Container(
                        alignment=ft.Alignment.CENTER,
                        content=self._build_icon_button(section),
                    )
                    for section in NAV_SECTIONS
                ],
                ft.Container(expand=True),
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=self._build_logout_button(),
                ),
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=self._build_toggle_button(),
                ),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _build_logout_button(self) -> ft.IconButton:
        def on_click(_e: ft.ControlEvent) -> None:
            if self._on_logout:
                self._on_logout()

        return ft.IconButton(
            icon=ft.Icons.LOGOUT,
            icon_size=20,
            tooltip="Cerrar sesión",
            icon_color=ft.Colors.ERROR,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            on_click=on_click,
        )

    def _build_toggle_button(self) -> ft.IconButton:
        def on_click(e: ft.ControlEvent) -> None:
            if self._on_toggle_menu:
                self._on_toggle_menu()

        self._toggle_btn = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            icon_size=18,
            tooltip="Colapsar menú",
            icon_color=theme.RAIL_ICON_DEFAULT,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            on_click=on_click,
        )
        return self._toggle_btn

    def update_toggle_icon(self, collapsed: bool) -> None:
        """Sincroniza el ícono del botón de colapso con el estado actual del menú."""
        if self._toggle_btn:
            self._toggle_btn.icon = ft.Icons.CHEVRON_RIGHT if collapsed else ft.Icons.CHEVRON_LEFT
            self._toggle_btn.tooltip = "Expandir menú" if collapsed else "Colapsar menú"
            self._toggle_btn.update()

    def set_active(self, section_id: str) -> None:
        self._active_section_id = section_id
        for section in NAV_SECTIONS:
            btn = self._buttons[section.id]
            selected = section.id == section_id
            btn.selected = selected
            btn.icon = self._icon(
                section.selected_icon if selected else section.icon
            )
            btn.icon_color = (
                theme.RAIL_ICON_SELECTED if selected else theme.RAIL_ICON_DEFAULT
            )
            btn.bgcolor = theme.RAIL_BTN_SELECTED_BG if selected else None
