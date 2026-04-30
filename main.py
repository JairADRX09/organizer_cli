import argparse
import logging
import sys
from utilidades import configurar_logging
from sincronizador import sincronizar
from limpiador import limpiar
from reportes import generar_reporte, reporte_limpieza


def cmd_sync(args):
    """Ejecuta el subcomando sync."""
    logging.info(
        f"subcomando: sync | origen={args.origen} | "
        f"destino={args.destino} | dry_run={args.dry_run}"
    )
    operaciones = sincronizar(args.origen, args.destino, dry_run=args.dry_run)

    if args.dry_run:
        print("\n[DRY_RUN] Operaciones que se ejecutarian:")
    else:
        print("\nSincronizacion completada:")

    print(f"  Copiados:     {operaciones['copiados']}")
    print(f"  Actualizados: {operaciones['actualizados']}")
    print(f"  Errores:      {operaciones['errores']}")


def cmd_clean(args):
    """Ejecuta el subcomando clean"""
    from reportes import reporte_limpieza

    logging.info(
        f"subcomando: clean | carpeta={args.carpeta} | dry_run={args.dry_run}"
    )

    print(reporte_limpieza(args.carpeta))

    confirmacion = "s"
    if not args.dry_run and not args.forzar:
        confirmacion = input("\n¿Proceder con la limpieza? (s/n): ").strip().lower()

    if args.dry_run:
        print("\n[DRY_RUN] Operaciones que se ejecutarian:")
        limpiar(args.carpeta, dry_run=True)
    elif confirmacion == "s":
        operaciones = limpiar(args.carpeta)
        print(f"\nLimpieza completada:")
        print(f"  Eliminados:  {operaciones['eliminados']}")
        print(f"  Errores:    {operaciones['errores']}")
    else:
        print("Operacion cancelada.")


def cmd_report(args):
    """Ejecuta el subcomando report."""
    logging.info(
        f"Subcomando: report | origen={args.origen} | destino={args.destino}"
    )
    reporte = generar_reporte(args.origen, args.destino)
    print(reporte)


def construir_parser():
    """Construye el parser de argumentos con subcomandos."""
    parser = argparse.ArgumentParser(
        prog="sincronizador",
        description="Sincronizador y limpiador de directorios CLI"
    )

    subparsers = parser.add_subparsers(dest="subcomando", required=True)

    #Subcomando: sync
    parser_sync = subparsers.add_parser(
        "sync",
        help="Sincroniza origen -> destino"
    )
    parser_sync.add_argument("--origen", required=True, help="Directorio fuente")
    parser_sync.add_argument("--destino", required=True, help="Directorio destino")
    parser_sync.add_argument(
        "--dry-run", action="store_true",
        help="Simula la operacion sin ejecutar cambios"
    )

    #Subcomando: clean
    parser_clean = subparsers.add_parser(
        "clean",
        help="Elimina archivos basura de una carpeta"
    )
    parser_clean.add_argument("--carpeta", required=True, help="Carpeta a limpiar")
    parser_clean.add_argument(
        "--dry-run", action="store_true",
        help="Simula la limpieza sin eliminar nada"
    )
    parser_clean.add_argument(
        "--forzar", action="store_true",
        help="ejecuta sin pedir confirmacion"
    )

    # Subcomando: report
    parser_report = subparsers.add_parser(
        "report",
        help="Genera reporte de diferencias entre dos directorios"
    )
    parser_report.add_argument("--origen", required=True, help="Primer directorio")
    parser_report.add_argument("--destino", required=True, help="Segundo directorio")

    return parser


def main():
    configurar_logging()
    parser = construir_parser()
    args = parser.parse_args()

    comandos = {
        "sync": cmd_sync,
        "clean": cmd_clean,
        "report": cmd_report
    }

    comando = comandos.get(args.subcomando)
    if comando:
        comando(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
