import flet as ft


class PeopleDataTable(ft.Column):
    def __init__(
        self,
        on_delete_click: callable,
        on_filter_change: callable,
        on_training_click: callable = None,   # opcional: None si la view no lo soporta
    ):
        self._on_delete_click   = on_delete_click
        self._on_filter_change  = on_filter_change
        self._on_training_click = on_training_click

        # Filtro e información de registros
        self._filter_input = ft.TextField(
            hint_text="Filtrar...",
            prefix_icon=ft.Icons.SEARCH,
            width=240,
            dense=True,
            on_change=self._on_filter_changed,
        )
        self._count_text = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)

        # Columnas — "Capacitaciones" solo aparece si on_training_click fue pasado
        base_columns = [
            ft.DataColumn(ft.Text("DNI")),
            ft.DataColumn(ft.Text("Nombre Completo")),
            ft.DataColumn(ft.Text("Empresa")),
            ft.DataColumn(ft.Text("Cargo")),
            ft.DataColumn(ft.Text("Fecha")),
        ]
        if self._on_training_click:
            base_columns.append(ft.DataColumn(ft.Text("Capacitaciones")))
        base_columns.append(ft.DataColumn(ft.Text("")))

        self._table = ft.DataTable(
            columns=base_columns,
            rows=[],
            heading_row_color=ft.Colors.SURFACE_CONTAINER,
            divider_thickness=0,
        )

        self._table_container = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[self._table],
        )

        self._empty_state = ft.Container(
            padding=ft.Padding(left=0, top=48, right=0, bottom=48),
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=44, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text("Sin usuarios registrados", size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
            ),
        )

        table_header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Text("Registros locales", size=14, weight=ft.FontWeight.W_600),
                        self._count_text,
                    ],
                ),
                self._filter_input,
            ],
        )

        super().__init__(
            expand=True,
            spacing=12,
            controls=[
                table_header,
                ft.Container(expand=True, content=self._table_container),
            ],
        )

    def get_filter_value(self) -> str:
        return self._filter_input.value.strip().lower()

    def _on_filter_changed(self, e) -> None:
        self._on_filter_change()

    def update_records(self, people: list, total_count: int) -> None:
        filter_val = self.get_filter_value()

        rows = []
        for person in people:
            full_name = f"{person.nombres} {person.apellido_paterno}"
            if person.apellido_materno:
                full_name += f" {person.apellido_materno}"

            cells = [
                ft.DataCell(ft.Text(person.nro_documento, selectable=True, size=13)),
                ft.DataCell(ft.Text(full_name, weight=ft.FontWeight.W_500, size=13)),
                ft.DataCell(ft.Text(person.empresa or "—", size=13)),
                ft.DataCell(ft.Text(person.cargo or "—", size=13)),
                ft.DataCell(ft.Text(person.created_at or "—", size=12, color=ft.Colors.ON_SURFACE_VARIANT)),
            ]

            # Celda "Ver cursos" solo si la view pasó el callback
            if self._on_training_click:
                cells.append(
                    ft.DataCell(
                        ft.TextButton(
                            "Ver cursos",
                            icon=ft.Icons.SCHOOL_OUTLINED,
                            on_click=lambda _, c=person.cod_persona, n=full_name: self._on_training_click(c, n),
                        )
                    )
                )

            # Celda eliminar — siempre presente, sin cambios
            cells.append(
                ft.DataCell(
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_size=18,
                        icon_color=ft.Colors.ERROR,
                        tooltip="Eliminar",
                        on_click=lambda _, d=person.nro_documento, n=full_name: self._on_delete_click(d, n),
                    )
                )
            )

            rows.append(ft.DataRow(cells=cells))

        self._table.rows = rows

        shown = len(people)
        if filter_val:
            self._count_text.value = f"{shown} de {total_count}"
        else:
            self._count_text.value = f"{total_count} registros"

        self._table_container.controls = [self._empty_state] if not rows else [self._table]
        if getattr(self, "_page", None):
            self.update()