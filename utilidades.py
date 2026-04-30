import hashlib
import logging
from pathlib import Path

def hash_archivo(ruta):
    """Calcula el MD5 de un archivo.
    Lee en bloques de 8KB para no cargar archivos grandes en memoria.
    Retorna el hash hex o None si el archivo no puede leerse."""
    hasher = hashlib.md5()
    try:
        with open(ruta, "rb") as f:
            while bloque := f.read(8192):
                hasher.update(bloque)
        return hasher.hexdigest()
    except (IOError, PermissionError) as e:
        logging.warning(f"No se pudo leer {ruta}: {e}")
        return None
    

def obtener_archivos(carpeta):
    """Escanea una carpeta recursivamente.
    Retorna diccionario {ruta_relativa: ruta_absoluta}."""
    carpeta = Path(carpeta)
    archivos = {}

    for ruta_abs in carpeta.rglob("*"):
        if ruta_abs.is_file():
            ruta_rel = ruta_abs.relative_to(carpeta)
            archivos[str(ruta_rel)] = ruta_abs

    return archivos


def formatear_tamano(bytes_size):
    """Convierte bytes a formato legible (KB, MB, GB)."""
    for unidad in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unidad}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"


def configurar_logging(nivel=logging.INFO):
    """Configura el sistema de logging.
    Escribe en archivo y en consola simultaneamente."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=nivel,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler("logs/operaciones.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )