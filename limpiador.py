import logging
from pathlib import Path


ARCHIVOS_BASURA = {
    ".DS_Store", "Thumbs.db", "desktop.ini",
    "._.DS_Store", "Icon\r"
}

EXTENSIONES_TEMPORALES = {
    ".tmp", ".temp", ".bak", ".swp", ".swo",
    ".pyc", ".pyo", ".log~"
}

CARPETAS_BASURA = {
    "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "git"
}

def escanear_basura(carpeta):
    """Escanea una carpeta e identifica archivos candidatos a eliminar.
    Retorna diccionario clasificado por tipo de basura."""
    carpeta = Path(carpeta)
    resultado = {
        "archivos_sistema": [],
        "archivos_temporales": [],
        "archivos_vacios": [],
        "carpetas_basura": []
    }

    for ruta in carpeta.rglob("*"):
        if ruta.is_file():
            if ruta.name in ARCHIVOS_BASURA:
                resultado["archivos_sistema"].append(ruta)

            elif ruta.suffix.lower() in EXTENSIONES_TEMPORALES:
                resultado["archivos_temporales"].append(ruta)
            
            elif ruta.stat().st_size == 0:
                resultado["archivos_vacios"].append(ruta)

        elif ruta.is_dir():
            if ruta.name in CARPETAS_BASURA:
                resultado["carpetas_basura"].append(ruta)

    total = sum(len(v) for v in resultado.values())
    logging.info(f"Escaneo completo en {carpeta} - {total} elemento(s) candidato(s)")

    return resultado


def limpiar(carpeta, dry_run=False):
    """Elimina archivos basura detectados en la carpeta.
    dry_run=True muestra que se eliminaria din ejecutar."""
    import shutil

    modo = "[DRY_RUN] " if dry_run else ""
    basura = escanear_basura(carpeta)
    operaciones = {"eliminados": 0, "errores": 0}

    for ruta in basura["archivos_sistema"] + basura["archivos_temporales"] + basura["archivos_vacios"]:
        logging.info(f"{modo}ELIMINAR archivo: {ruta}")
        if not dry_run:
            try:
                ruta.unlink()
                operaciones["eliminados"] += 1
            except (IOError, PermissionError) as e:
                logging.error(f"Error al eliminar {ruta}: {e}")
                operaciones["errores"] += 1
        else:
            operaciones["eliminados"] += 1

    for ruta in basura["carpetas_basura"]:
        logging.info(f"{modo}ELIMINAR carpeta: {ruta}")
        if not dry_run:
            try:
                shutil.rmtree(ruta)
                operaciones["eliminados"] += 1
            except (IOError, PermissionError) as e:
                logging.error(f"Error al eliminar {ruta}: {e}")
                operaciones["errores"] += 1
        else:
            operaciones["eliminados"] += 1
    
    logging.info(
        f"{modo}Limpieza completa - "
        f"Eliminados: {operaciones['eliminados']} | "
        f"Errores: {operaciones['errores']}"
    )

    return operaciones