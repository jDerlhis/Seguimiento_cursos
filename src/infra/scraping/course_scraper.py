import os
import csv
import json
import uuid
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from infra.auth.session_store import session_path
from shared.logger import get_logger
from data.models.course_model import Course

logger = get_logger(__name__)

def fetch_courses_via_scraping(dni: str, headless: bool = True) -> list[Course]:
    """
    Automatiza el navegador para descargar el reporte de capacitacion del usuario,
    lo parsea y devuelve una lista de objetos Course.
    """
    path_sesion = session_path()
    if not os.path.exists(path_sesion):
        raise RuntimeError("No se encontró sesión activa. Inicia sesión en HSEC Web primero.")

    courses = []
    
    # Crear un directorio temporal para la descarga
    temp_dir = Path(os.environ.get("TEMP", "/tmp")) / f"hsec_downloads_{uuid.uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=['--start-maximized'])
        context = browser.new_context(
            storage_state=path_sesion,
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        page = context.new_page()
        page.set_default_timeout(30000)

        try:
            logger.info(f"Navegando a reporte para DNI {dni}...")
            url_reporte = "https://antapaccay.sam.glencore.net/hsec_web/#/ReportePersonalCapacitado"
            
            try:
                page.goto(url_reporte, wait_until="networkidle", timeout=20000)
            except Exception:
                pass
            
            page.wait_for_timeout(3000)
            
            # 1. Abrir modal
            btn_add = page.locator("span.pi-user-plus").first
            btn_add.wait_for(state="visible", timeout=15000)
            btn_add.click()
            
            # 2. Ingresar DNI (es el tercer input de la fila)
            input_dni = page.locator("input[placeholder*='Documento']:not([disabled]):not([readonly])").first
            input_dni.wait_for(state="visible", timeout=10000)
            input_dni.fill(dni)
            
            # 3. Buscar
            btn_buscar = page.locator("span.ui-button-text.ui-clickable", has_text="Buscar").first
            btn_buscar.click()
            page.wait_for_timeout(2000)
            
            # 4. Seleccionar fila
            fila_resultado = page.locator("tbody tr").first
            try:
                fila_resultado.wait_for(state="visible", timeout=5000)
                fila_resultado.click()
            except Exception:
                logger.warning(f"No se encontraron resultados en el modal para DNI {dni}")
                browser.close()
                return []
            
            # 5. Clic Seleccionar
            btn_seleccionar = page.locator("span.ui-button-text.ui-clickable", has_text="Seleccionar").first
            btn_seleccionar.wait_for(state="visible", timeout=5000)
            btn_seleccionar.click()
            page.wait_for_timeout(2000)
            
            # 6. Hacer clic en "Ver reporte" (reporte simple)
            btn_reporte = page.locator("span.ui-button-text.ui-clickable", has_text="Ver reporte").first
            try:
                btn_reporte.wait_for(state="visible", timeout=5000)
                btn_reporte.click()
            except Exception:
                logger.warning(f"No apareció el botón 'Ver reporte' para DNI {dni}")
                browser.close()
                return []
                
            page.wait_for_timeout(5000)
            
            # 7. Interactuar con el iframe de SSRS para descargar el CSV
            frame = page.frame_locator("ssrs-reportviewer iframe").first
            cuerpo_iframe = frame.locator("body")
            cuerpo_iframe.wait_for(state="attached", timeout=15000)
            
            export_menu = frame.locator("img[alt*='Export'], img[title*='Export'], a[title*='Export']").first
            if not export_menu.is_visible(timeout=10000):
                raise RuntimeError("No se encontró el menú de exportación en el iframe del reporte.")
                
            export_menu.click()
            page.wait_for_timeout(1000)
            
            csv_link = frame.locator("a[title*='CSV'], a:has-text('CSV')").first
            if not csv_link.is_visible():
                raise RuntimeError("No se encontró la opción CSV en el menú de exportación.")
                
            logger.info("Descargando archivo CSV desde SSRS...")
            with page.expect_download(timeout=30000) as dl_info:
                csv_link.click()
                
            dl = dl_info.value
            out_file = temp_dir / f"report_{dni}.csv"
            dl.save_as(str(out_file))
            logger.info(f"CSV descargado en {out_file}")
            
            # 8. Parsear el CSV a objetos Course
            courses = parse_courses_from_csv(str(out_file), dni)
            
            # Limpiar archivo temporal
            try:
                os.remove(out_file)
                temp_dir.rmdir()
            except Exception as e:
                logger.warning(f"No se pudo eliminar el archivo temporal: {e}")
                
        except Exception as ex:
            logger.error(f"Error durante el scraping para DNI {dni}: {ex}")
            raise
        finally:
            browser.close()
            
    return courses


def parse_courses_from_csv(file_path: str, dni: str) -> list[Course]:
    courses = []
    with open(file_path, "r", encoding="utf-8-sig", errors="ignore") as f:
        reader = csv.reader(f)
        # El CSV de SSRS incluye metadatos (como Nombre y DNI) antes de los headers de la tabla
        # Buscaremos la línea que empieza con 'fecha' para empezar a leer los datos
        reading_data = False
        
        for row in reader:
            if not row:
                continue
                
            if row[0].strip().lower() == "fecha":
                reading_data = True
                continue
                
            if reading_data and len(row) >= 8:
                # Orden esperado de columnas:
                # fecha, Textbox17 (duracion), Descripcion, AreaCapacita1, modEstado, Nota, minimoAprobado1, fecVencimiento
                try:
                    c = Course(
                        id=None,
                        dni=dni,
                        fecha=row[0].strip(),
                        duracion=row[1].strip(),
                        descripcion=row[2].strip(),
                        area=row[3].strip(),
                        estado=row[4].strip(),
                        nota=row[5].strip(),
                        minimo_aprobado=row[6].strip(),
                        fecha_vencimiento=row[7].strip()
                    )
                    courses.append(c)
                except Exception as ex:
                    logger.warning(f"Fila ignorada por formato incorrecto: {row} - Error: {ex}")
                    
    logger.info(f"Se extrajeron {len(courses)} cursos del CSV.")
    return courses
