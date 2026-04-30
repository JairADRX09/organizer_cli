import shutil
import logging
from pathlib import Path
from comparador import comparar_directorios
from utilidades import obtener_archivos


def sincronizar(origen, destino, dry_run=False):
    """Sincroniza origen -> destino.
    Copia archivos nuevos y modificados. No elimina nada en destino.
    dry_run=True muestra las operaciones sin ejecutarlas."""
    origen = Path(origen)
    destino = Path(destino)
    modo = "[DRY-RUN] " if dry_run else ""

    resultado = comparar_directorios(origen, destino)
    operaciones = {"copiados": 0, "actualizados": 0, "errores": 0}

    # Copiar archivos que solo existen en origen
    for rel in resultado["solo_en_origen"]:
        src = origen / rel
        dst = destino / rel

        logging.info(f"{modo}COPIAR: {rel}")

        if not dry_run:
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                operaciones["copiados"] += 1
            except (IOError, PermissionError) as e:
                logging.error(f"Error al copiar {rel}: {e}")
                operaciones["errores"] += 1
        else:
            operaciones["copiados"] += 1

    # Actualizar archivos modificados
    for item in resultado["modificados"]:
        rel = item["ruta"]
        src = origen / rel
        dst = destino / rel

        logging.info(f"{modo}ACTUALIZAR: {rel}")

        if not dry_run:
            try:
                shutil.copy2(src, dst)
                operaciones["actualizados"] += 1
            except (IOError, PermissionError) as e:
                logging.error(f"Error al actualizar {rel}: {e}")
                operaciones["errores"] += 1
        else:
            operaciones["actualizados"] += 1
    
    logging.info(
        f"{modo}Sincronizacion completa - "
        f"Copiados: {operaciones['copiados']} | "
        f"Actualizados: {operaciones['actualizados']} | "
        f"Errores: {operaciones['errores']}"
    )

    return operaciones

            