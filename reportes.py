import logging
from pathlib import Path
from comparador import comparar_directorios, detectar_duplicados_internos
from utilidades import obtener_archivos, formatear_tamano


def generar_reporte(origen, destino):
    """Genera un reporte completo de diferencias entre dos directorios.
    Retorna el reporte como string y lo escribe en logs/."""
    resultado = comparar_directorios(origen, destino)

    lineas = [
        "=" * 60,
        "  REPORTE DE COMPARACION DE DIRECTORIOS",
        "=" * 60,
        f"  Origen: {origen}",
        f"  Destino: {destino}",
        "",
        f"Archivos solo en origen:   {len(resultado['solo_en_origen'])}",
        f"Archivos solo en destino:  {len(resultado['solo_en_destino'])}",
        f"Archivos identicos:        {len(resultado['identicos'])}",
        f"Archivos modificados:      {len(resultado['modificados'])}",
        f"Archivos duplicados:       {len(resultado['duplicados'])}",
        ""
    ]

    if resultado["solo_en_origen"]:
        lineas.append("--- Solo en origen:")
        for rel in resultado["solo_en_origen"]:
            ruta_abs = Path(origen) / rel
            tamano = formatear_tamano(ruta_abs.stat().st_size)
            lineas.append(f"  + {rel} ({tamano})")
        lineas.append("")

    if resultado["solo_en_destino"]:
        lineas.append("-- Solo en destino:")
        for rel in resultado["solo_en_destino"]:
            lineas.append(f"  - {rel}")
        lineas.append("")

    if resultado["modificados"]:
        lineas.append("--- Modificados (mismo path, distinto contenido):")
        for item in resultado["modificados"]:
            lineas.append(f"   ~ {item['ruta']}")
        lineas.append("")

    if resultado["duplicados"]:
        lineas.append("-- Duplicados (mismo contenido, distinto path):")
        for item in resultado["duplicados"]:
            lineas.append(f"  = {item['origen']} -> {item['destino']}")
        lineas.append("")

    lineas.append("=" * 60)
    reporte = "\n".join(lineas)

    reporte_path = Path("logs") / "ultimo_reporte.txt"
    reporte_path.parent.mkdir(exist_ok=True)
    reporte_path.write_text(reporte, encoding="utf-8")
    logging.info(f"Reporte guardado en {reporte_path}")

    return reporte

def reporte_limpieza(carpeta):
    """Genera reporte de archivos basura encontrados en una carpeta."""
    from limpiador import escanear_basura
    from utilidades import formatear_tamano

    basura = escanear_basura(carpeta)

    lineas = [
        "=" *60,
        "  REPORTE DE LIMPIEZA",
        "=" * 60,
        f"  Carpeta: {carpeta}",
        ""
    ]

    categorias = {
        "archivos_sistema": "Archivos del sistema",
        "archivos_temporales": "Archivos temporales",
        "archivos_vacios": "Archivos vacios",
        "carpetas_basura": "Carpetas de cache/build"
    }

    for clave, nombre in categorias.items():
        items = basura[clave]
        if items:
            lineas.append(f"-- {nombre} ({len(items)}):")
            for ruta in items:
                if ruta.is_file():
                    tamano = formatear_tamano(ruta.stat().st_size)
                    lineas.append(f"  {ruta.name} ({tamano})")
                else:
                    lineas.append(f"  {ruta.name}/")
            lineas.append("")
    
    total = sum(len(v) for v in basura.values())
    if total == 0:
        lineas.append(" ✅ No se encontro basura.")

    lineas.append("=" * 60)
    return "\n".join(lineas)
