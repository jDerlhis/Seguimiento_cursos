import flet as ft

from app.features.hsec.hsec_view import HsecView
from app.features.users.presentation.views.search_person_view import SearchPersonView
from app.features.users.presentation.views.import_person_view import ImportPersonView

HSEC_KEY = "hsec"
SEARCH_PERSON_KEY = "searchPerson"
IMPORT_PERSON_KEY = "importPerson"


def build_content(item_key: str, page: ft.Page) -> ft.Control:
    if item_key == HSEC_KEY:
        return HsecView(page)
    elif item_key == SEARCH_PERSON_KEY:
        return SearchPersonView(page)
    elif item_key == IMPORT_PERSON_KEY:
        return ImportPersonView(page)

    return ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        content=ft.Text(
            "Selecciona «HSEC Web» en Datos → Fuentes para iniciar sesión o «Buscar» en Usuarios.",
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
        ),
    )

