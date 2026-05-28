"""
Script de descubrimiento del flujo de la pagina ReportePersonalCapacitado
Usa Playwright para capturar capturas de pantalla en cada paso del flujo
y descubrir la estructura del modal y los pasos del proceso.
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright
from infra.auth.session_store import session_path, has_saved_session

def step_screenshot(page, name):
    """Toma una captura y la guarda con el nombre del paso."""
    path = f"debug_step_{name}.png"
    page.screenshot(path=path, full_page=True)
    print(f"  [Screenshot guardado: {path}]")

def main():
    print("=== Descubriendo flujo de ReportePersonalCapacitado ===")

    if not has_saved_session():
        print("Error: No hay sesion guardada.")
        return 1

    dni = "43556935"
    path_sesion = session_path()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(path_sesion))
        page = context.new_page()

        # PASO 1: Navegar a la pagina principal del reporte
        print("\n[PASO 1] Navegando a la pagina...")
        url = "https://antapaccay.sam.glencore.net/hsec_web/#/ReportePersonalCapacitado"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except Exception:
            print("  Timeout en goto, continuando...")
        page.wait_for_timeout(3000)
        step_screenshot(page, "01_pagina_inicial")

        # Imprimir el HTML del contenido para analizar los selectores
        print("\n[PASO 1] Analizando los elementos de la pagina...")
        inner_html = page.locator("app-root").inner_html()
        with open("debug_html.txt", "w", encoding="utf-8") as f:
            f.write(inner_html)
        print("  HTML guardado en debug_html.txt")

        # PASO 2: Encontrar e imprimir todos los inputs y botones
        print("\n[PASO 2] Elementos encontrados en la pagina:")
        inputs = page.locator("input").all()
        for i, inp in enumerate(inputs):
            try:
                placeholder = inp.get_attribute("placeholder") or ""
                tipo = inp.get_attribute("type") or ""
                print(f"  Input {i}: type={tipo}, placeholder='{placeholder}'")
            except Exception:
                pass

        botones = page.locator("button, span.ui-button-text").all()
        for i, btn in enumerate(botones):
            try:
                texto = btn.inner_text().strip()
                if texto:
                    print(f"  Boton {i}: '{texto}'")
            except Exception:
                pass

        # PASO 3: Intentar hacer clic en el icono del modal de persona
        # (Segun la captura, hay un boton con icono de persona a la derecha del input "Escribe aqui")
        print("\n[PASO 3] Intentando abrir el modal de busqueda por persona...")
        
        # Los botones en PrimeNG tienen iconos en spans con fa-* o pi-*
        # Buscar botones con icono de persona/usuario
        posibles_botones_icono = [
            "button:has(.fa-user)",
            "button:has(.pi-user)",
            "button:has(.pi-search)",
            "button.ui-button:last-of-type",
            ".ui-inputgroup button",
            "[class*='person'] button",
            "p-autocomplete button",
            "button[icon]",
        ]

        boton_encontrado = None
        for selector in posibles_botones_icono:
            try:
                el = page.locator(selector).first
                if el.is_visible(timeout=1000):
                    boton_encontrado = selector
                    print(f"  Boton encontrado con selector: {selector}")
                    break
            except Exception:
                pass

        if boton_encontrado:
            page.locator(boton_encontrado).first.click()
            page.wait_for_timeout(2000)
            step_screenshot(page, "03_despues_click_modal_btn")
        else:
            print("  No se encontro el boton del modal con selectores comunes.")
            
            # Listar todos los botones con sus atributos completos
            print("\n  Dump completo de botones:")
            botones_todos = page.locator("button").all()
            for i, btn in enumerate(botones_todos):
                try:
                    outer = btn.evaluate("el => el.outerHTML")
                    print(f"  Button {i}: {outer[:200]}")
                except Exception:
                    pass

        # Revisar si aparecio el modal
        print("\n[PASO 4] Revisando si aparecio el modal...")
        modal_visible = page.locator(".ui-dialog, p-dialog, [role='dialog']").is_visible(timeout=3000)
        if modal_visible:
            print("  Modal encontrado!")
            step_screenshot(page, "04_modal_abierto")
            modal_html = page.locator(".ui-dialog, p-dialog, [role='dialog']").first.inner_html()
            with open("debug_modal_html.txt", "w", encoding="utf-8") as f:
                f.write(modal_html)
            print("  HTML del modal guardado en debug_modal_html.txt")
        else:
            print("  No se detecto modal abierto.")

        browser.close()
    print("\n=== Fin del descubrimiento ===")

if __name__ == "__main__":
    sys.exit(main())
