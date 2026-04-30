import logging
from pathlib import Path
from utilidades import hash_archivo, obtener_archivos


def comparar_directorios(origen, destino):
    """Compara dos directorios y clasifica sus archivos.
    
    Retorna diccionario con:
    - solo_en_origen: archivos que no existen en destino
    - solo_en_destino: archivos que no existen en origen
    - identicos: misma ruta relativa y mismo hash
    - modificados: misma ruta relativa pero hash diferentes
    - duplicados: mismo hash solo distinta ruta (renombrados o movidos)
    """
    logging.info(f"Comparando: {origen} ↔ {destino}")

    archivos_origen = obtener_archivos(origen)
    archivos_destino = obtener_archivos(destino)

    hashes_origen = {}
    for rel, abs_path in archivos_origen.items():
        h = hash_archivo(abs_path)
        if h:
            hashes_origen[h] = rel

    hashes_destino = {}
    for rel, abs_path in archivos_destino.items():
        h = hash_archivo(abs_path)
        if h:
            hashes_destino[h] = rel

    resultado = {
        "solo_en_origen": [],
        "solo_en_destino": [],
        "identicos": [],
        "modificados": [],
        "duplicados": []
    }

    for rel, abs_path in archivos_origen.items():
        if rel in archivos_destino:
            hash_orig = hash_archivo(abs_path)
            hash_dest = hash_archivo(archivos_destino[rel])

            if hash_orig == hash_dest:
                resultado["identicos"].append(rel)
            else:
                resultado["modificados"].append({
                    "ruta": rel,
                    "hash_origen": hash_orig,
                    "hash_destino": hash_dest
                })
        else:
            hash_orig = hash_archivo(abs_path)
            if hash_orig and hash_orig in hashes_destino:
                resultado["duplicados"].append({
                    "origen": rel,
                    "destino": hashes_destino[hash_orig],
                    "hash": hash_orig
                })
            else:
                resultado["solo_en_origen"].append(rel)

    for rel in archivos_destino:
        if rel not in archivos_origen:
            hash_dest = hash_archivo(archivos_destino[rel])
            if not (hash_dest and hash_dest in hashes_origen):
                resultado["solo_en_destino"].append(rel)

    logging.info(
        f"Comparacion completa - "
        f"Solo en origen: {len(resultado['solo_en_origen'])} | "
        f"Solo en destino: {len(resultado['solo_en_destino'])} | "
        f"Identicos: {len(resultado['identicos'])} | "
        f"Modificados: {len(resultado['modificados'])} | "
        f"Duplicados: {len(resultado['duplicados'])}"
    )

    return resultado


def detectar_duplicados_internos(carpeta):
    """Detecta archivos duplicados DENTRO de una misma carpeta.
    Agrupa por hash - cada grupo con mas de un archivo son duplicados."""
    archivos = obtener_archivos(carpeta)
    grupos_hash = {}

    for rel, abs_path in archivos.items():
        h = hash_archivo(abs_path)
        if h:
            if h not in grupos_hash:
                grupos_hash[h] = []
            grupos_hash[h].append(rel)

    duplicados = {
        h: rutas for h, rutas in grupos_hash.items()
        if len(rutas) > 1
    }

    logging.info(
        f"Duplicados internos en {carpeta}: "
        f"{len(duplicados)} grupos con contenido identico"
    )

    return duplicados