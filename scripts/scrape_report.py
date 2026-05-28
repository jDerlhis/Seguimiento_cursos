"""
Scraper definitivo para ReportePersonalCapacitado
Descubierto el flujo real del HTML con discover_flow.py

El flujo real de la pagina es:
1. La pagina tiene un componente <app-person-select> con disabled-search="true"
2. Hay 2 botones de icono en esa sección:
   - Botón 1: icon="pi pi-times" (X) para limpiar la selección
   - Botón 2: icon="pi pi-user-plus" con tooltip "Haga click para seleccionar personal" -> ESTE abre el modal
3. El modal contiene un input con placeholder "N° Documento" para buscar por DNI
4. Se hace clic en "Buscar", se selecciona la persona de la tabla
5. Luego se hace clic en "Ver reporte" o "Ver reporte detallado"

SELECTORES CONFIRMADOS (de HTML real):
- Botón abrir modal: span.pi-user-plus  (el span interno del botón)
- Input DNI en modal: input[placeholder*='Documento']:not([disabled]):not([readonly])
- Botón buscar en modal: span.ui-button-text con texto "Buscar"
- Tabla resultados: tbody tr
- Botón Ver reporte: span.pi-list (primero)
- Botón Ver reporte detallado: span.pi-list (segundo)
- El iframe SSRS: ssrs-reportviewer iframe
"""
import sys
import time
import urllib.parse as urlparse
from urllib.parse import parse_qs
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright
from infra.auth.session_store import session_path, has_saved_session

def main():
    print("=== Scraper Reporte Personal Capacitado ===")

    if not has_saved_session():
        print("Error: No hay sesion guardada.")
        return 1

    dni = "60295528"
    path_sesion = session_path()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(path_sesion))
        page = context.new_page()

        # PASO 1: Navegar
        print("[1] Navegando a la pagina...")
        try:
            page.goto(
                "https://antapaccay.sam.glencore.net/hsec_web/#/ReportePersonalCapacitado",
                wait_until="domcontentloaded",
                timeout=20000
            )
        except Exception:
            print("  goto timeout, continuando...")
        # Esperar a que Angular termine de renderizar los componentes
        print("  Esperando que Angular cargue los componentes (7s)...")
        page.wait_for_timeout(7000)

        # PASO 2: Click en boton "pi pi-user-plus" para abrir el modal de busqueda
        # Selector confirmado por HTML dump: button[ng-reflect-icon='pi pi-user-plus']
        print("[2] Abriendo modal de busqueda de persona...")
        # El span interno del botón tiene clase 'pi pi-user-plus'
        # Hacemos click directamente en el span (que es lo que abre el modal)
        print("  Haciendo click en span.pi-user-plus...")
        try:
            span_btn = page.locator("span.pi-user-plus")
            span_btn.wait_for(state="visible", timeout=10000)
            span_btn.click()
            print("  Click en span.pi-user-plus exitoso!")
        except Exception as e:
            page.screenshot(path="debug_err_modal.png")
            print(f"  Error abriendo modal: {e}")
            browser.close()
            return 1

        page.wait_for_timeout(2000)
        page.screenshot(path="debug_step_modal.png")
        print("  Screenshot guardado: debug_step_modal.png")

        # PASO 3: Escribir DNI en el input del modal
        # El modal tiene 4 inputs: Apellido Paterno (0), Apellido Materno (1), N° Documento (2), Nombres (3)
        # Usamos nth(2) para apuntar exactamente al campo N° Documento
        print(f"[3] Ingresando DNI: {dni}")
        try:
            input_dni = page.locator("input.ui-inputtext:not([disabled]):not([readonly])").nth(2)
            input_dni.wait_for(state="visible", timeout=5000)
            input_dni.fill(dni)
            print(f"  DNI '{dni}' ingresado.")
        except Exception as e:
            page.screenshot(path="debug_err_dni.png")
            print(f"  Error ingresando DNI: {e}")
            browser.close()
            return 1

        # PASO 4: Clic en "Buscar" dentro del modal
        print("[4] Haciendo clic en Buscar...")
        try:
            btn_buscar = page.locator("span.ui-button-text.ui-clickable", has_text="Buscar").first
            btn_buscar.click()
            page.wait_for_timeout(2000)
            page.screenshot(path="debug_step_buscar.png")
            print("  Busqueda enviada (screenshot: debug_step_buscar.png)")
        except Exception as e:
            page.screenshot(path="debug_err_buscar.png")
            print(f"  Error al hacer clic en Buscar: {e}")
            browser.close()
            return 1

        # PASO 5: Hacer clic en la primera fila del resultado para seleccionarla
        print("[5] Seleccionando fila de resultado...")
        try:
            primera_fila = page.locator("tbody tr").first
            primera_fila.wait_for(state="visible", timeout=5000)
            primera_fila.click()
            page.wait_for_timeout(1000)
            page.screenshot(path="debug_step_fila.png")
            print("  Fila seleccionada (screenshot: debug_step_fila.png)")
        except Exception as e:
            page.screenshot(path="debug_err_fila.png")
            print(f"  Error seleccionando fila: {e}")
            browser.close()
            return 1

        # PASO 6: Clic en "Seleccionar" para confirmar y cerrar el modal
        print("[6] Haciendo clic en Seleccionar...")
        try:
            btn_seleccionar = page.locator("span.ui-button-text.ui-clickable", has_text="Seleccionar").first
            btn_seleccionar.wait_for(state="visible", timeout=5000)
            btn_seleccionar.click()
            page.wait_for_timeout(2000)
            page.screenshot(path="debug_step_seleccionar.png")
            print("  Seleccionado! Modal cerrado (screenshot: debug_step_seleccionar.png)")
        except Exception as e:
            page.screenshot(path="debug_err_seleccionar.png")
            print(f"  Error al hacer clic en Seleccionar: {e}")
            browser.close()
            return 1

        # Verificar que el nombre aparece en el campo de persona
        try:
            nombre_persona = page.locator("input.ui-inputtext[readonly]").first.get_attribute("placeholder")
            print(f"  Campo persona: {nombre_persona}")
        except Exception:
            pass

        # PASO 6a: Hacer clic en "Ver reporte" y extraer datos via intercepción de red
        print("[6a] Haciendo clic en 'Ver reporte'...")
        try:
            btn_reporte = page.locator("span.ui-button-text", has_text="Ver reporte").first
            
            # Interceptar todas las peticiones de red ANTES de hacer click
            requests_capturadas = []
            def capturar_request(req):
                if "ReportViewerWebControl" in req.url or "Report.aspx" in req.url:
                    requests_capturadas.append(req.url)
            page.on("request", capturar_request)
            
            btn_reporte.click()
            page.wait_for_timeout(6000)
            page.remove_listener("request", capturar_request)
            page.screenshot(path="debug_step_reporte.png")

            print(f"  Peticiones SSRS capturadas: {len(requests_capturadas)}")
            for url in requests_capturadas[:5]:
                print(f"    - {url[:120]}")

            iframe_loc = page.locator("ssrs-reportviewer iframe")
            if iframe_loc.is_visible():
                src_reporte = iframe_loc.get_attribute("src")
                print(f"  iframe URL: {src_reporte}")
                # Intentar exportación desde DENTRO del contexto (con cookies activas)
                _export_desde_contexto(context, page, src_reporte, "reporte_simple")
            else:
                print("  iframe no apareció. Ver debug_step_reporte.png")
        except Exception as e:
            print(f"  Error en 'Ver reporte': {e}")

        # PASO 6b: Ver reporte detallado
        print("[6b] Haciendo clic en 'Ver reporte detallado'...")
        try:
            btn_detallado = page.locator("span.ui-button-text", has_text="Ver reporte detallado").first
            btn_detallado.click()
            page.wait_for_timeout(6000)
            page.screenshot(path="debug_step_detallado.png")

            iframe_loc = page.locator("ssrs-reportviewer iframe")
            if iframe_loc.is_visible():
                src_detallado = iframe_loc.get_attribute("src")
                print(f"  iframe URL: {src_detallado}")
                _export_desde_contexto(context, page, src_detallado, "reporte_detallado")
            else:
                print("  iframe no apareció. Ver debug_step_detallado.png")
        except Exception as e:
            print(f"  Error en 'Ver reporte detallado': {e}")

        browser.close()
    print("\n=== Fin del scraping ===")


def _export_desde_contexto(context, page, iframe_src, nombre):
    """
    Estrategia de interacción directa con el iframe a través de FrameLocator.
    """
    print(f"  Analizando iframe para reporte: {nombre}")
    try:
        frame = page.frame_locator("ssrs-reportviewer iframe").first
        
        # Esperar a que el cuerpo del iframe esté presente
        cuerpo_iframe = frame.locator("body")
        cuerpo_iframe.wait_for(state="attached", timeout=15000)
        
        html_iframe = cuerpo_iframe.inner_html()
        with open(f"{nombre}_iframe_dump.html", "w", encoding="utf-8", errors="ignore") as f:
            f.write(html_iframe)
        print(f"  HTML del iframe guardado en {nombre}_iframe_dump.html ({len(html_iframe)} bytes)")
        
        # Intentar buscar elementos de exportación comunes en SSRS
        export_menu = frame.locator("img[alt*='Export'], img[title*='Export'], a[title*='Export']").first
        if export_menu.is_visible(timeout=5000):
            print("  Botón de menú Export encontrado, haciendo click...")
            export_menu.click()
            page.wait_for_timeout(2000)
            
            # Buscar el enlace a CSV
            csv_link = frame.locator("a[title*='CSV'], a:has-text('CSV')").first
            if csv_link.is_visible():
                print("  Enlace CSV encontrado, iniciando descarga...")
                with page.expect_download(timeout=30000) as dl_info:
                    csv_link.click()
                dl = dl_info.value
                out_file = f"{nombre}.csv"
                dl.save_as(out_file)
                print(f"  [OK] CSV descargado y guardado en {out_file}")
            else:
                print("  Enlace CSV no encontrado en el menú.")
        else:
            print("  Botón de menú Export no encontrado en el iframe.")
            
    except Exception as ex:
        print(f"  Error interactuando con el iframe: {ex}")


if __name__ == "__main__":
    sys.exit(main())
