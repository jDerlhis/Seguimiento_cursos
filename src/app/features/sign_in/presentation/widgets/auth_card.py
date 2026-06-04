import flet as ft

from shared import theme


class AuthCard(ft.Container):
    """Tarjeta centrada para formularios de autenticación."""

    def __init__(self, title: str, subtitle: str, form: ft.Control, footer: ft.Control | None = None):
        logo = ft.Container(
            content=ft.Icon(ft.Icons.SCHOOL_ROUNDED, size=32, color=ft.Colors.ON_PRIMARY),
            width=68,
            height=68,
            border_radius=20,
            bgcolor=ft.Colors.PRIMARY,
            alignment=ft.Alignment(0, 0),
        )

        body_controls = [
            ft.Container(content=logo, alignment=ft.Alignment(0, 0)),
            ft.Container(height=4),
            ft.Text(
                title,
                size=28,
                weight=ft.FontWeight.W_700,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.ON_SURFACE,
            ),
            ft.Text(
                subtitle,
                size=13,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Divider(height=24, thickness=1, color=ft.Colors.OUTLINE_VARIANT),
            form,
        ]
        if footer:
            body_controls.append(ft.Divider(height=24, thickness=1, color=ft.Colors.OUTLINE_VARIANT))
            body_controls.append(footer)

        super().__init__(
            width=420,
            padding=ft.Padding.symmetric(horizontal=36, vertical=32),
            bgcolor=theme.MENU_BG,
            border_radius=20,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=32,
                color=ft.Colors.with_opacity(0.1, ft.Colors.SHADOW),
                offset=ft.Offset(0, 6),
            ),
            content=ft.Column(
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=body_controls,
            ),
        )
