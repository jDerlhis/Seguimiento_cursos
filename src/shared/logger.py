import logging
import sys
from pathlib import Path

# Buscamos la raíz del proyecto para colocar la carpeta de logs
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = _PROJECT_ROOT / "logs"

def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_filename: str = "pyflow.log"
) -> None:
    """
    Configura el sistema de loggers para todo el proyecto.
    Agrega un formateador premium y opcionalmente persiste los logs en un archivo.
    """
    # Evitar duplicar handlers si ya está configurado
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.setLevel(level)

    # Formateador con fecha y módulo
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # 1. Handler para Consola (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. Handler para Archivo (opcional)
    if log_to_file:
        try:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            log_path = LOGS_DIR / log_filename
            file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as ex:
            print(f"No se pudo inicializar el archivo de logs: {ex}", file=sys.stderr)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna una instancia de Logger con el nombre especificado.
    """
    return logging.getLogger(name)
