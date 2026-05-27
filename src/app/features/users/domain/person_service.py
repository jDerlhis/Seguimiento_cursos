import csv
from shared.logger import get_logger
from typing import Callable, Optional, Tuple
from app.features.users.domain import people_repository
from data.models.person_model import Person
from infra.scraping.hsec_api import fetch_person_from_api

logger = get_logger(__name__)

def get_or_fetch_person(dni: str) -> Tuple[Optional[Person], str]:
    """
    Busca una persona por su DNI.
    Primero busca en la base de datos local (SQLite).
    Si no existe localmente, la consulta a la API de HSEC y la guarda en SQLite.
    
    Retorna:
        (Person, "local") si ya existía en la DB local.
        (Person, "api") si se obtuvo de la API de HSEC y se guardó.
        (None, "not_found") si no existe en HSEC.
    """
    # 1. Comprobar base de datos local
    local_person = people_repository.get_person_by_dni(dni)
    if local_person:
        return local_person, "local"
        
    # 2. Consultar API de HSEC
    person_data = fetch_person_from_api(dni)
    if not person_data:
        return None, "not_found"
        
    # 3. Guardar en SQLite
    person = Person.from_api_dict(person_data)
    people_repository.insert_person(person)
    return person, "api"


def extract_dnis_from_file(file_path: str) -> list[str]:
    """
    Extrae números de DNI (8 dígitos numéricos) de un archivo CSV o Excel (.xlsx).
    """
    dnis = []
    ext = file_path.split(".")[-1].lower()
    
    if ext == "csv":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                for cell in row:
                    val = str(cell).strip()
                    if len(val) == 8 and val.isdigit():
                        dnis.append(val)
    elif ext in ("xlsx", "xls"):
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True)
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                for cell in row:
                    if cell is not None:
                        val = str(cell).strip()
                        if len(val) == 8 and val.isdigit():
                            dnis.append(val)
                            
    # Mantener orden y remover duplicados
    seen = set()
    unique_dnis = []
    for d in dnis:
        if d not in seen:
            seen.add(d)
            unique_dnis.append(d)
    return unique_dnis


def import_people_from_file(
    file_path: str, 
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> dict:
    """
    Procesa un archivo (CSV o Excel) buscando DNIs y registrándolos en la base de datos.
    Sigue la lógica de verificar localmente antes de consultar la API externa.
    
    progress_callback firma: (index_actual, total_dnis, dni_actual)
    
    Retorna un diccionario con el resumen de la importación:
        {
            "total": int,
            "added": int,
            "not_found": int,
            "already_exists": int
        }
    """
    dnis = extract_dnis_from_file(file_path)
    if not dnis:
        return {"total": 0, "added": 0, "not_found": 0, "already_exists": 0}
        
    added = 0
    not_found = 0
    already_exists = 0
    
    total = len(dnis)
    
    for idx, dni in enumerate(dnis, start=1):
        if progress_callback:
            progress_callback(idx, total, dni)
            
        try:
            person, source = get_or_fetch_person(dni)
            if source == "local":
                already_exists += 1
            elif source == "api" and person:
                added += 1
            else:
                not_found += 1
        except Exception as ex:
            logger.warning(f"Error procesando DNI {dni} en importación masiva: {ex}")
            not_found += 1
            
    return {
        "total": total,
        "added": added,
        "not_found": not_found,
        "already_exists": already_exists
    }
