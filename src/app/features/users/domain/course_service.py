from typing import List, Tuple
from shared.logger import get_logger
from app.features.users.domain import course_repository
from infra.scraping.course_scraper import fetch_courses_via_scraping
from data.models.course_model import Course

logger = get_logger(__name__)

def sync_courses_for_dni(dni: str, headless: bool = True) -> Tuple[List[Course], str]:
    """
    Sincroniza los cursos de una persona:
    1. Llama al scraper (Playwright) para descargar y extraer datos desde HSEC.
    2. Guarda los cursos extraídos en la base de datos local SQLite.
    3. Devuelve los cursos sincronizados y un mensaje de estado.
    
    Retorna:
        (List[Course], mensaje_de_estado)
    """
    logger.info(f"Iniciando sincronización de cursos para DNI {dni}...")
    
    try:
        # 1. Obtener cursos via Scraping
        courses = fetch_courses_via_scraping(dni, headless=headless)
        
        if not courses:
            return [], "No se encontraron cursos o hubo un problema al obtenerlos."
            
        # 2. Guardar en base de datos
        course_repository.insert_courses(courses)
        
        # 3. Leer de la base de datos para devolverlos consistentes
        saved_courses = course_repository.get_courses_by_dni(dni)
        
        return saved_courses, f"Se sincronizaron {len(saved_courses)} cursos exitosamente."
        
    except Exception as e:
        logger.error(f"Error sincronizando cursos para {dni}: {e}")
        raise RuntimeError(f"Error en sincronización: {e}")

def get_local_courses(dni: str) -> List[Course]:
    """
    Obtiene los cursos de una persona solo desde la base de datos local.
    """
    return course_repository.get_courses_by_dni(dni)
