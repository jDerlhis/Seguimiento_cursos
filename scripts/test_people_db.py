import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from data.database import init_db
from data import people_repository
from data.models import Person

def main():
    print("=== Test People Database and Repository ===")
    
    # 1. Inicializar base de datos y migrar tabla people
    print("Inicializando base de datos...")
    init_db()
    
    # 2. Listar personas (debe estar vacía al inicio o tener registros previos)
    people = people_repository.list_people()
    print(f"Número de personas registradas: {len(people)}")
    
    # 3. Insertar una persona de prueba
    test_dni = "99999999"
    p = Person(
        id=None,
        cod_persona="TEST_01",
        nombres="JUAN CARLOS",
        apellido_paterno="PÉREZ",
        apellido_materno="GÓMEZ",
        cod_proveedor=None,
        empresa="TEST EMPRESA S.A.",
        cod_cargo="CARGO_TEST",
        cargo="Operario",
        flag_persistente=None,
        cod_tipo_persona=2,
        nro_documento=test_dni,
        tipo_documento="DNI"
    )
    
    print(f"Insertando persona de prueba con DNI {test_dni}...")
    people_repository.insert_person(p)
    
    # 4. Obtener persona por DNI
    fetched = people_repository.get_person_by_dni(test_dni)
    if fetched:
        print(f"Obtenido con éxito: {fetched.nombres} {fetched.apellido_paterno} de {fetched.empresa}")
        assert fetched.nombres == "JUAN CARLOS"
        assert fetched.nro_documento == test_dni
    else:
        print("Error: No se pudo recuperar la persona insertada.")
        return 1
        
    # 5. Listar personas de nuevo
    people = people_repository.list_people()
    print(f"Número de personas registradas tras inserción: {len(people)}")
    
    # 6. Eliminar persona de prueba
    print(f"Eliminando persona de prueba con DNI {test_dni}...")
    people_repository.delete_person(test_dni)
    
    # 7. Verificar eliminación
    fetched = people_repository.get_person_by_dni(test_dni)
    if not fetched:
        print("Eliminación verificada correctamente.")
    else:
        print("Error: La persona no fue eliminada.")
        return 1
        
    print("¡Base de datos y Repositorio funcionando al 100%!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
