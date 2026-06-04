import flet as ft

from shared import theme

from app.common.modules.sidebar.sidebar_menu import SidebarMenu
from app.common.modules.sidebar.sidebar_rail import SidebarRail
from app.common.modules.sidebar.navigation import (
    DEFAULT_ITEM_KEY,
    DEFAULT_SECTION_ID,
    NAV_SECTIONS,
)


def _build_content(item_key: str, page: ft.Page) -> ft.Control:
    if item_key == "hsec":
        from app.features.hsec.hsec_view import build_hsec_view

        return build_hsec_view(page)

    if item_key == "hsec_sync":
        from app.features.hsec.presentation.views.hsec_sync_view import build_hsec_sync_view

        return build_hsec_sync_view(page)

    item_title = "Inicio"
    for section in NAV_SECTIONS:
        for menu in section.menus:
            for item in menu.items:
                if item.key == item_key:
                    item_title = item.title
                    break

    return ft.Column(
        expand=True,
        spacing=8,
        controls=[
            ft.Text(item_title, size=20, weight=ft.FontWeight.W_600),
            ft.Text(
                "Contenido en desarrollo.",
                size=14,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ],
    )


def _find_item_title(section_id: str, item_key: str) -> tuple[str, str]:
    for section in NAV_SECTIONS:
        if section.id != section_id:
            continue
        for menu in section.menus:
            for item in menu.items:
                if item.key == item_key:
                    return section.label, item.title
    return "Pyflow", "Inicio"


class AppShell(ft.Row):
    def __init__(self, page: ft.Page, on_logout=None):
        self._page = page
        self._on_logout = on_logout
        self._active_section_id = DEFAULT_SECTION_ID
        self._active_item_key = DEFAULT_ITEM_KEY

        self._rail = SidebarRail(
            on_section_change=self._on_section_change,
            active_section_id=self._active_section_id,
            on_toggle_menu=self._on_toggle_menu,
            on_logout=self._handle_logout,
        )
        self._menu = SidebarMenu(
            section_id=self._active_section_id,
            active_item_key=self._active_item_key,
            on_item_select=self._on_item_select,
            on_toggle=self._rail.update_toggle_icon,
            on_logout=self._handle_logout,
        )
        self._content_title = ft.Text(size=28, weight=ft.FontWeight.W_600)
        self._content_subtitle = ft.Text(size=14, color=ft.Colors.ON_SURFACE_VARIANT)
        self._content_body = ft.Container(expand=True)
        self._content_area = ft.Container(
            expand=True,
            bgcolor=theme.CONTENT_BG,
            padding=32,
            content=ft.Column(
                expand=True,
                controls=[
                    self._content_title,
                    self._content_subtitle,
                    ft.Divider(height=24, color=ft.Colors.OUTLINE_VARIANT),
                    self._content_body,
                ],
            ),
        )

        super().__init__(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    bgcolor=theme.SIDEBAR_BG,
                    content=ft.Row(
                        spacing=0,
                        controls=[
                            self._rail,
                            ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE_VARIANT),
                            self._menu,
                        ],
                    ),
                ),
                ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE_VARIANT),
                self._content_area,
            ],
        )
        self._render_content()

    def _render_content(self) -> None:
        self._content_body.content = _build_content(self._active_item_key, self._page)
        self._refresh_content_header()

    def _refresh_content_header(self) -> None:
        section_label, item_title = _find_item_title(
            self._active_section_id, self._active_item_key
        )
        self._content_title.value = item_title
        self._content_subtitle.value = f"{section_label} › {item_title}"

    def _on_section_change(self, section_id: str) -> None:
        is_same_section = (section_id == self._active_section_id)

        if is_same_section:
            self._menu.toggle_collapse()
            return

        self._active_section_id = section_id
        section = next(s for s in NAV_SECTIONS if s.id == section_id)
        if section.menus and section.menus[0].items:
            self._active_item_key = section.menus[0].items[0].key

        self._rail.set_active(section_id)

        # Si el menú está colapsado, expandirlo al cambiar de sección
        if self._menu._collapsed:
            self._menu.toggle_collapse()

        self._menu.update_section(section_id, self._active_item_key)
        self._refresh_content_header()
        self._render_content()
        self._page.update()

    def _on_item_select(self, item_key: str, section_id: str) -> None:
        self._active_item_key = item_key
        self._active_section_id = section_id
        self._menu.update_section(section_id, item_key)
        self._refresh_content_header()
        self._render_content()
        self._page.update()

    def _on_toggle_menu(self) -> None:
        self._menu.toggle_collapse()

    def _handle_logout(self) -> None:
        from app.features.sign_in.domain import auth_service

        auth_service.logout()
        if self._on_logout:
            self._on_logout()


def build_shell(page: ft.Page, on_logout=None) -> AppShell:
    return AppShell(page, on_logout=on_logout)
