import flet as ft

import shared.theme as theme
from app.common.modules.sidebar.navigation import NAV_SECTIONS, NavMenu, NavSection


class SidebarMenu(ft.Container):
    """
    Panel lateral de navegación de segundo nivel.
    Expandido: muestra encabezados de grupo + ítems con texto.
    Colapsado: se oculta por completo, dejando solo el rail principal visible.
    """

    def __init__(
        self,
        section_id: str,
        active_item_key: str,
        on_item_select,
        on_toggle: callable = None,
    ):
        self._section_id = section_id
        self._active_item_key = active_item_key
        self._on_item_select = on_item_select
        self._on_toggle = on_toggle
        self._section = self._find_section(section_id)
        self._collapsed = False

        # Vista expandida
        self._header_label = ft.Text(
            self._section.label,
            size=15,
            weight=ft.FontWeight.W_600,
            color=theme.MENU_HEADER_COLOR,
        )
        self._header = ft.Container(
            padding=ft.Padding(left=12, top=0, right=12, bottom=8),
            content=self._header_label,
        )
        self._menu_list = ft.ListView(
            spacing=4,
            padding=ft.Padding(left=0, top=4, right=0, bottom=8),
            controls=[self._build_menu_tile(menu) for menu in self._section.menus],
        )

        super().__init__(
            width=theme.MENU_WIDTH,
            bgcolor=theme.MENU_BG,
            padding=ft.Padding(left=8, top=12, right=8, bottom=12),
            content=self._build_content(),
            visible=True,
            animate_size=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        )

    # ─── Builders ─────────────────────────────────────────────────────────────

    def _find_section(self, section_id: str) -> NavSection:
        for section in NAV_SECTIONS:
            if section.id == section_id:
                return section
        return NAV_SECTIONS[0]

    def _get_icon(self, name: str | None, size: int = 20) -> ft.Icon | None:
        if not name:
            return None
        try:
            return ft.Icon(getattr(ft.Icons, name.upper()), size=size, color=theme.RAIL_ICON_DEFAULT)
        except AttributeError:
            return None

    def _build_menu_tile(self, menu: NavMenu) -> ft.Control:
        """Tile expandido con encabezado de grupo e ítems con texto."""
        leading = self._get_icon(menu.icon, size=16)
        leading_controls = [leading] if leading else []

        if menu.items:
            header_row = ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    *leading_controls,
                    ft.Text(
                        menu.title,
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=theme.MENU_SUBTITLE_COLOR,
                    ),
                ],
            )
            items_column = ft.Column(
                spacing=2,
                controls=[self._build_item_tile(item) for item in menu.items],
            )
            return ft.Column(
                spacing=4,
                controls=[
                    ft.Container(
                        padding=ft.Padding(left=4, top=8, right=4, bottom=4),
                        content=header_row,
                    ),
                    items_column,
                ],
            )

        return ft.ListTile(
            title=ft.Text(menu.title, size=13),
            leading=leading,
            dense=True,
            shape=ft.RoundedRectangleBorder(radius=8),
        )

    def _build_item_tile(self, item) -> ft.ListTile:
        """Ítem expandido: ícono + texto."""
        selected = item.key == self._active_item_key
        item_icon = self._get_icon(item.icon, size=18)

        def on_click(e: ft.ControlEvent) -> None:
            self._on_item_select(item.key, self._section.id)

        return ft.ListTile(
            title=ft.Text(
                item.title,
                size=13,
                weight=ft.FontWeight.W_500 if selected else ft.FontWeight.W_400,
            ),
            leading=item_icon,
            selected=selected,
            dense=True,
            shape=ft.RoundedRectangleBorder(radius=8),
            selected_tile_color=theme.ITEM_SELECTED_BG,
            selected_color=theme.ITEM_SELECTED_COLOR,
            on_click=on_click,
        )

    def _build_content(self) -> ft.Control:
        self._divider = ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT)
        self._menu_container = ft.Container(
            expand=True,
            content=self._menu_list,
        )
        return ft.Column(
            controls=[
                self._header,
                self._divider,
                self._menu_container,
            ],
            spacing=0,
            expand=True,
        )

    # ─── Colapso ──────────────────────────────────────────────────────────────

    def toggle_collapse(self) -> None:
        """Alterna entre vista expandida y vista colapsada (oculta por completo)."""
        self._collapsed = not self._collapsed

        # Se oculta/muestra el contenedor completo
        self.visible = not self._collapsed
        self.update()

        if self._on_toggle:
            self._on_toggle(self._collapsed)

    # ─── Actualización de sección ─────────────────────────────────────────────

    def update_section(self, section_id: str, active_item_key: str) -> None:
        self._section_id = section_id
        self._active_item_key = active_item_key
        self._section = self._find_section(section_id)
        self._header_label.value = self._section.label
        self._menu_list.controls = [self._build_menu_tile(menu) for menu in self._section.menus]
        self.update()
