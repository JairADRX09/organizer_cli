# Sincronizador y Limpiador de Directorios CLI

Herramienta de línea de comandos para comparar, sincronizar y limpiar directorios. Detecta diferencias entre carpetas por contenido (hash MD5), no solo por nombre — identifica archivos renombrados, movidos, modificados y duplicados aunque tengan paths distintos. Incluye modo simulación (`--dry-run`) en todas las operaciones destructivas.

## Casos de Uso

- **Sincronización de backups:** Mantener una carpeta de respaldo actualizada respecto a la carpeta de trabajo, copiando solo los archivos nuevos o modificados.
- **Detección de duplicados entre proyectos:** Identificar archivos con el mismo contenido distribuidos en distintas rutas antes de una reorganización.
- **Limpieza de repositorios y proyectos:** Eliminar `__pycache__`, `.DS_Store`, `Thumbs.db`, archivos `.tmp` y otros residuos del sistema que no deben subir a control de versiones.
- **Auditoría antes de entregas:** Generar un reporte de qué archivos difieren entre dos versiones de un directorio antes de sincronizar.
- **Mantenimiento de carpetas de descargas:** Detectar y eliminar archivos vacíos, temporales y duplicados acumulados con el tiempo.

## Instalación

No requiere dependencias externas. Solo librería estándar de Python 3.8+.

```bash
git clone https://github.com/JairADRX09/sincronizador-cli
cd sincronizador_cli
python main.py --help
```

## Uso

```bash
# Comparar dos directorios y generar reporte
python main.py report --origen ./proyecto --destino ./backup

# Sincronizar origen → destino (simulación)
python main.py sync --origen ./proyecto --destino ./backup --dry-run

# Sincronizar de verdad
python main.py sync --origen ./proyecto --destino ./backup

# Limpiar archivos basura (simulación)
python main.py clean --carpeta ./descargas --dry-run

# Limpiar sin pedir confirmación
python main.py clean --carpeta ./descargas --forzar
```

## Subcomandos

| Subcomando | Descripción | Flags |
|---|---|---|
| `report` | Compara dos directorios y muestra diferencias | `--origen`, `--destino` |
| `sync` | Copia archivos nuevos/modificados de origen a destino | `--origen`, `--destino`, `--dry-run` |
| `clean` | Detecta y elimina archivos basura | `--carpeta`, `--dry-run`, `--forzar` |

## Flujo de Datos

```
Terminal (argparse)
       │
       ▼
   main.py ──────────────── Parsea subcomando y flags, dispatch a cmd_*
       │
       ├──► comparador.py ── Escanea ambas carpetas, calcula hashes MD5
       │         │
       │         ▼
       │    utilidades.py ── hash_archivo(), obtener_archivos(), formatear_tamano()
       │
       ├──► sincronizador.py ── Copia/actualiza archivos según resultado del comparador
       │
       ├──► limpiador.py ──── Detecta y elimina archivos basura por tipo
       │
       └──► reportes.py ───── Genera reporte legible en terminal y en logs/

   logging ────────────────── Transversal: registra toda operación con timestamp
       │
       └──► logs/operaciones.log   (append, todas las sesiones)
            logs/ultimo_reporte.txt (sobreescrito por cada report)
```

**Flujo de comparación por hash:**
```
archivo en disco
       │
       ▼
hash_archivo() → lee en bloques de 8KB → MD5 hexdigest
       │
       ▼
comparar_directorios() → cruza hashes y paths → clasifica en 5 categorías
```

## Estructura del Proyecto

```
sincronizador_cli/
├── main.py              # Punto de entrada, argparse con subcomandos
├── comparador.py        # Comparación de directorios por hash MD5
├── sincronizador.py     # Operaciones de copia y actualización
├── limpiador.py         # Detección y eliminación de archivos basura
├── reportes.py          # Generación de reportes en texto
├── utilidades.py        # Hashing, escaneo de carpetas, formateo, logging
└── logs/
    ├── operaciones.log      # Log acumulativo de todas las operaciones
    └── ultimo_reporte.txt   # Último reporte generado por `report`
```

## Responsabilidad de Cada Módulo

### main.py — Interfaz CLI y dispatch
Punto de entrada. Construye el parser con `argparse` y sus tres subcomandos. Cada subcomando tiene su propio conjunto de flags. El dispatch usa un diccionario de funciones `cmd_*`.

**Funciones:**
- `construir_parser()` → Define parser principal y tres subparsers con sus flags.
- `cmd_sync(args)` → Llama a `sincronizar()` y muestra resumen de operaciones.
- `cmd_clean(args)` → Muestra reporte de limpieza, pide confirmación si no hay `--forzar`, llama a `limpiar()`.
- `cmd_report(args)` → Llama a `generar_reporte()` e imprime el resultado.
- `main()` → Configura logging, parsea argumentos, ejecuta el comando.

### comparador.py — Motor de comparación
Núcleo del sistema. Compara dos directorios cruzando rutas relativas y hashes MD5. La clasificación por hash permite detectar archivos renombrados o movidos que un comparador por nombre no detectaría.

**Funciones:**
- `comparar_directorios(origen, destino)` → Escanea ambas carpetas, calcula hashes, clasifica cada archivo en una de 5 categorías. Retorna diccionario con listas por categoría.
- `detectar_duplicados_internos(carpeta)` → Agrupa archivos de una misma carpeta por hash. Retorna diccionario `{hash: [rutas]}` donde cada grupo tiene más de un archivo.

**Las 5 categorías de clasificación:**

| Categoría | Criterio |
|---|---|
| `solo_en_origen` | Path existe en origen, no en destino, hash único |
| `solo_en_destino` | Path existe en destino, no en origen, hash único |
| `identicos` | Mismo path en ambos, mismo hash |
| `modificados` | Mismo path en ambos, hash diferente |
| `duplicados` | Hash idéntico, paths distintos (renombrado/movido) |

### sincronizador.py — Operaciones de sincronización
Copia archivos de origen a destino. Opera sobre el resultado de `comparar_directorios` — nunca escanea directorios directamente. No elimina archivos en destino: sincronización unidireccional aditiva.

**Funciones:**
- `sincronizar(origen, destino, dry_run)` → Copia `solo_en_origen`, actualiza `modificados`. Con `dry_run=True` solo registra en log sin ejecutar. Retorna `{"copiados", "actualizados", "errores"}`.

### limpiador.py — Detección y eliminación de basura
Clasifica archivos candidatos a eliminar en 4 categorías usando conjuntos de nombres y extensiones conocidas.

**Constantes:**
- `ARCHIVOS_BASURA` → Nombres exactos: `.DS_Store`, `Thumbs.db`, `desktop.ini`, etc.
- `EXTENSIONES_TEMPORALES` → Extensiones: `.tmp`, `.bak`, `.swp`, `.pyc`, `.pyo`, etc.
- `CARPETAS_BASURA` → Nombres de directorios: `__pycache__`, `.pytest_cache`, `node_modules`, etc.

**Funciones:**
- `escanear_basura(carpeta)` → Recorre la carpeta con `rglob`. Clasifica cada archivo/directorio en su categoría. Retorna diccionario con listas de rutas `Path`.
- `limpiar(carpeta, dry_run)` → Llama a `escanear_basura`, ejecuta `unlink()` en archivos y `shutil.rmtree()` en carpetas. Con `dry_run=True` solo registra. Retorna `{"eliminados", "errores"}`.

### reportes.py — Generación de reportes
Formatea la salida de `comparar_directorios` y `escanear_basura` en texto legible para terminal y para archivo.

**Funciones:**
- `generar_reporte(origen, destino)` → Llama al comparador, construye reporte con resumen numérico y detalle por categoría. Escribe en `logs/ultimo_reporte.txt`. Retorna el reporte como string.
- `reporte_limpieza(carpeta)` → Llama a `escanear_basura`, formatea los resultados por categoría con tamaños de archivo. Retorna string — no escribe a disco.

### utilidades.py — Funciones transversales
Sin dependencias internas. Usado por todos los módulos.

**Funciones:**
- `hash_archivo(ruta)` → Lee el archivo en bloques de 8KB, actualiza MD5 incrementalmente. Retorna hex digest o `None` si no puede leerse.
- `obtener_archivos(carpeta)` → Escanea recursivamente con `rglob`. Retorna `{str(ruta_relativa): Path(ruta_absoluta)}`.
- `formatear_tamano(bytes_size)` → Convierte bytes a B/KB/MB/GB/TB con una decimal.
- `configurar_logging(nivel)` → Configura handlers simultáneos: archivo (`logs/operaciones.log`) y consola. Crea el directorio `logs/` si no existe.

## Estrategia de Comparación

El sistema usa **hash MD5 como identidad de contenido**, no el nombre del archivo. Esto resuelve casos que un comparador por nombre no puede manejar:

```
carpeta_a/logo.png         (hash: abc123)
carpeta_b/icons/logo.png   (hash: abc123)
→ Detectado como DUPLICADO, no como archivo nuevo
```

```
carpeta_a/config.json      (hash: def456)
carpeta_b/config.json      (hash: 789ghi)  ← mismo nombre, distinto contenido
→ Detectado como MODIFICADO
```

**Lectura en bloques de 8KB:** En lugar de cargar el archivo completo en memoria, `hash_archivo` lee y procesa el archivo en fragmentos. Permite calcular el hash de archivos de varios GB sin consumir RAM proporcional.

## Logging

Todas las operaciones se registran en `logs/operaciones.log` con timestamp, nivel y mensaje. El archivo crece acumulativamente — no se sobreescribe entre sesiones.

```
2026-04-26 20:12:38 [INFO] Comparando: things ↔ things1
2026-04-26 20:12:38 [INFO] Comparación completa — Solo en origen: 0 | ...
2026-04-26 20:12:38 [INFO] Reporte guardado en logs\ultimo_reporte.txt
```

El log simultáneo en consola permite ver el progreso en tiempo real sin necesidad de abrir el archivo.

## Limitaciones Conocidas

- **Sincronización unidireccional:** `sync` copia de origen a destino. No hay modo bidireccional ni detección de conflictos.
- **Sin deshacer:** Las operaciones de `sync` y `clean` no tienen reversión automática. El `--dry-run` es la única protección antes de ejecutar.
- **MD5 no es criptográficamente seguro:** Para comparación de archivos es suficiente, pero no debe usarse para verificación de integridad en contextos de seguridad.
- **Rendimiento en redes lentas:** El hash requiere leer el contenido completo del archivo. Sobre redes o discos lentos, comparar directorios grandes puede ser lento.
- **`CARPETAS_BASURA` no incluye `.git`:** Eliminar `.git` destruiría el historial del repositorio. Está excluido intencionalmente.

## Mejoras Pendientes para Revisitar en Fases Futuras

- Modo sincronización bidireccional con detección de conflictos.
- Archivo de log de operaciones ejecutadas para poder revertirlas (`--undo`).
- Soporte para filtros por extensión o por fecha de modificación en `sync`.
- Progreso visual con barra de porcentaje para directorios grandes.
- Tests con `pytest` usando directorios temporales (`tmp_path` fixture) (Fase 5: semana 19).
- Empaquetado como herramienta instalable con `pip` y entry point CLI (Fase 6: semana 22).