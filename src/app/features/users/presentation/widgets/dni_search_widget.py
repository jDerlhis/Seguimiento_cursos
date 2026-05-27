import flet as ft
from app.features.users.domain import people_repository

class DniSearchWidget(ft.Column):
    def __init__(self, on_search_api: callable, on_person_found_locally: callable):
        self._on_search_api = on_search_api
        self._on_person_found_locally = on_person_found_locally
        
        # Estado
        self._suggestions: list = []

        # Controles
        self._dni_input = ft.TextField(
            label="DNI (8 dígitos)",
            hint_text="Ej. 46897109",
            max_length=8,
            prefix_icon=ft.Icons.BADGE_OUTLINED,
            input_filter=ft.NumbersOnlyInputFilter(),
            on_change=self._on_dni_change,
            on_submit=self._on_submit,
            expand=True,
        )
        
        self._search_button = ft.FilledButton(
            "Buscar",
            icon=ft.Icons.PERSON_SEARCH_OUTLINED,
            on_click=self._on_search_click,
            disabled=True,  # Deshabilitado por defecto
        )

        # Contenedor de Sugerencias
        self._suggestions_list = ft.ListView(
            spacing=2,
            height=120,
            padding=ft.Padding(4, 4, 4, 4),
        )
        
        self._suggestions_container = ft.Container(
            content=self._suggestions_list,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(8),
            visible=False,
            padding=ft.Padding(0, 0, 0, 0),
            margin=ft.Margin(0, 2, 0, 0),
        )

        super().__init__(
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[self._dni_input, self._search_button],
                ),
                self._suggestions_container,
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True,
        )

    def set_disabled(self, disabled: bool) -> None:
        self._dni_input.disabled = disabled
        if not disabled:
            # Mantener el botón buscar deshabilitado excepto si se cumple la condición de no existir
            self._validate_dni_state()
        else:
            self._search_button.disabled = True
        if getattr(self, "_page", None):
            self.update()

    def get_value(self) -> str:
        return self._dni_input.value.strip()

    def set_value(self, value: str) -> None:
        self._dni_input.value = value
        self._validate_dni_state()
        if getattr(self, "_page", None):
            self.update()

    def clear(self) -> None:
        self._dni_input.value = ""
        self._dni_input.error_text = None
        self._suggestions_container.visible = False
        self._search_button.disabled = True
        if getattr(self, "_page", None):
            self.update()

    def _on_dni_change(self, e) -> None:
        dni = self._dni_input.value.strip()
        self._validate_dni_state()
        self._update_suggestions(dni)
        if getattr(self, "_page", None):
            self.update()

    def _validate_dni_state(self) -> None:
        dni = self._dni_input.value.strip()
        
        if not dni:
            self._dni_input.error_text = None
            self._search_button.disabled = True
            return

        if len(dni) < 8:
            self._dni_input.error_text = f"{len(dni)}/8 dígitos"
            self._search_button.disabled = True
            return

        # Si tiene 8 dígitos
        self._dni_input.error_text = None
        
        # Buscar localmente
        local_person = people_repository.get_person_by_dni(dni)
        if local_person:
            # Existe localmente: deshabilitar botón y notificar
            self._search_button.disabled = True
            self._on_person_found_locally(local_person)
        else:
            # NO existe localmente: habilitar botón
            self._search_button.disabled = False

    def _update_suggestions(self, prefix: str) -> None:
        if not prefix or len(prefix) >= 8:
            self._suggestions_container.visible = False
            return

        # Listar personas registradas localmente y filtrar por el prefijo
        people = people_repository.list_people()
        matches = [
            p for p in people 
            if p.nro_documento.startswith(prefix)
        ]

        if not matches:
            self._suggestions_container.visible = False
            return

        self._suggestions_list.controls = [
            ft.ListTile(
                title=ft.Text(f"{p.nro_documento} - {p.nombres} {p.apellido_paterno}", size=13),
                dense=True,
                hover_color=ft.Colors.SURFACE_CONTAINER_LOW,
                on_click=lambda _, person=p: self._select_suggestion(person),
            )
            for p in matches[:5]  # Mostrar máximo 5
        ]
        self._suggestions_container.visible = True

    def _select_suggestion(self, person) -> None:
        self._dni_input.value = person.nro_documento
        self._suggestions_container.visible = False
        self._validate_dni_state()
        if getattr(self, "_page", None):
            self.update()

    def _on_search_click(self, e) -> None:
        dni = self.get_value()
        if len(dni) == 8 and not self._search_button.disabled:
            self._on_search_api(dni)

    def _on_submit(self, e) -> None:
        # Al presionar Enter, si está habilitado el botón, buscar
        if not self._search_button.disabled:
            self._on_search_click(None)
