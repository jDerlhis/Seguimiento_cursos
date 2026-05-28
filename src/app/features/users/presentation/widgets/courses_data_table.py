import flet as ft
from data.models.course_model import Course

class CoursesDataTable(ft.Column):
    def __init__(self):
        super().__init__(expand=True)
        self._table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Fecha")),
                ft.DataColumn(ft.Text("Curso / Descripción")),
                ft.DataColumn(ft.Text("Área")),
                ft.DataColumn(ft.Text("Nota")),
                ft.DataColumn(ft.Text("Estado")),
                ft.DataColumn(ft.Text("Vencimiento")),
            ],
            rows=[],
            expand=True,
            column_spacing=20,
        )

        self.controls = [
            ft.Row([ft.Text("Historial de Capacitaciones", size=18, weight="bold")]),
            ft.Container(
                content=self._table,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=ft.BorderRadius.all(8),
                padding=0,
                expand=True,
            ),
        ]

    def update_records(self, courses: list[Course]):
        rows = []
        for course in courses:
            color = ft.Colors.GREEN if course.estado.lower() == "aprobado" else ft.Colors.RED if course.estado.lower() in ("desaprobado", "vencido") else ft.Colors.ON_SURFACE
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(course.fecha)),
                        ft.DataCell(ft.Text(course.descripcion, weight="bold")),
                        ft.DataCell(ft.Text(course.area)),
                        ft.DataCell(ft.Text(course.nota)),
                        ft.DataCell(ft.Text(course.estado, color=color, weight="bold")),
                        ft.DataCell(ft.Text(course.fecha_vencimiento)),
                    ]
                )
            )
        self._table.rows = rows
        if getattr(self, "_page", None) or getattr(self, "page", None):
            self.update()

    def clear(self):
        self._table.rows = []
        if getattr(self, "_page", None) or getattr(self, "page", None):
            self.update()
