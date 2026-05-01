# Readme Investigate — Sincronizador y Limpiador de Directorios CLI (Semana 9)

Catálogo de cada recurso de Python utilizado en el proyecto. Cada entrada explica qué es, cómo funciona, dónde se usa y por qué se eligió.

---

## Módulos de Librería Estándar

### pathlib
**Qué es:** Módulo para manipulación de rutas del sistema de archivos orientado a objetos. Introducido en Python 3.4 como alternativa moderna a `os.path`.

**Cómo funciona:** Representa rutas como objetos `Path` en lugar de strings. Las operaciones sobre rutas se expresan como métodos y operadores en lugar de funciones de módulo.

**Dónde se usa:** En todos los módulos del proyecto.

**Métodos y propiedades utilizados:**

- `Path(string)` → Construye un objeto Path desde un string. Normaliza separadores según el OS (`/` en Linux, `\` en Windows).

```python
# utilidades.py
carpeta = Path(carpeta)    # "mis/archivos" → Path object
log_dir = Path("logs")     # string → Path
```

- `Path / string` → Operador `/` para concatenar rutas. Más legible que `os.path.join`.

```python
# sincronizador.py
src = origen / rel         # Path("carpeta_a") / "archivo.txt"
dst = destino / rel        # → Path("carpeta_a/archivo.txt")

# reportes.py
ruta_abs = Path(origen) / rel
reporte_path = Path("logs") / "ultimo_reporte.txt"
```

- `ruta.is_file()` → Retorna `True` si la ruta existe y es un archivo (no directorio ni symlink).
- `ruta.is_dir()` → Retorna `True` si la ruta existe y es un directorio.

```python
# utilidades.py
for ruta_abs in carpeta.rglob("*"):
    if ruta_abs.is_file():      # Filtra solo archivos
        ...
```

- `ruta.rglob(patron)` → Escaneo recursivo. Retorna generador de todas las rutas que coinciden con el patrón en la carpeta y sus subdirectorios.

```python
# utilidades.py
carpeta.rglob("*")    # Todos los archivos y carpetas recursivamente

# limpiador.py
carpeta.rglob("*")    # Mismo patrón para escanear basura
```

**`rglob("*")` vs `glob("*")`:**

| Método | Alcance |
|---|---|
| `glob("*")` | Solo el directorio actual (no subdirectorios) |
| `rglob("*")` | Recursivo — equivale a `glob("**/*")` |

- `ruta.relative_to(base)` → Retorna la ruta relativa respecto a `base`. Esencial para comparar archivos entre dos carpetas distintas.

```python
# utilidades.py
ruta_rel = ruta_abs.relative_to(carpeta)
# Path("/home/user/docs/archivo.txt").relative_to("/home/user/docs")
# → Path("archivo.txt")
```

- `ruta.parent` → La carpeta que contiene la ruta.
- `ruta.parent.mkdir(parents=True, exist_ok=True)` → Crea el directorio y todos sus padres si no existen. `exist_ok=True` evita error si ya existe.

```python
# sincronizador.py
dst.parent.mkdir(parents=True, exist_ok=True)
# Si dst es "backup/sub/archivo.txt", crea "backup/sub/" si no existe
```

- `ruta.stat().st_size` → Tamaño del archivo en bytes. `stat()` retorna un objeto con metadata del archivo del OS.
- `ruta.name` → Solo el nombre del archivo con extensión, sin la ruta completa.
- `ruta.suffix` → La extensión del archivo incluyendo el punto (`.txt`, `.pyc`).
- `ruta.unlink()` → Elimina el archivo. Equivalente a `os.remove()`.
- `ruta.write_text(texto, encoding)` → Escribe texto en el archivo. Crea o sobreescribe.
- `log_dir.mkdir(exist_ok=True)` → Crea el directorio. `exist_ok=True` no lanza error si ya existe.

---

### hashlib
**Qué es:** Módulo para funciones de hash criptográfico. En este proyecto se usa MD5 para comparación de contenido de archivos — no para seguridad.

**Cómo funciona MD5:** Transforma datos de cualquier tamaño en un digest de 128 bits (32 caracteres hexadecimales). La misma entrada siempre produce el mismo output. Cualquier cambio mínimo en el archivo produce un digest completamente distinto.

**Dónde se usa:** En `utilidades.py`, función `hash_archivo`.

```python
# utilidades.py
import hashlib

def hash_archivo(ruta):
    hasher = hashlib.md5()          # Crea objeto hasher vacío
    with open(ruta, "rb") as f:
        while bloque := f.read(8192):   # Lee 8KB a la vez
            hasher.update(bloque)        # Actualiza el hash incremental
    return hasher.hexdigest()            # Retorna string hex de 32 chars
```

**Por qué lectura incremental en bloques:** `hasher.update()` acepta datos parciales y mantiene el estado interno. Esto permite calcular el hash de un archivo de 10GB leyendo solo 8KB en memoria a la vez, en lugar de cargar el archivo completo.

**Por qué MD5 y no SHA-256:** Para comparación de archivos, la velocidad importa más que la resistencia criptográfica. MD5 es más rápido que SHA-256 y suficientemente único para detectar diferencias entre archivos. No se usa para seguridad en este contexto.

**MD5 como identidad de contenido:**
```
archivo_a.txt (contenido: "hola") → hash: "5d41402abc4b2a76b9719d911017c592"
archivo_b.txt (contenido: "hola") → hash: "5d41402abc4b2a76b9719d911017c592"
→ Mismo hash = mismo contenido, aunque los nombres sean distintos
```

---

### shutil
**Qué es:** Módulo para operaciones de alto nivel sobre archivos y directorios: copiar, mover, eliminar árboles de directorios.

**Dónde se usa:** En `sincronizador.py` y `limpiador.py`.

**Funciones utilizadas:**

- `shutil.copy2(src, dst)` → Copia el archivo preservando metadata (fechas de modificación y acceso, permisos). La `2` indica que copia tanto el contenido como los metadatos.

```python
# sincronizador.py
shutil.copy2(src, dst)    # Copia preservando fecha de modificación original
```

**`shutil.copy2` vs `shutil.copy`:**

| Función | Copia contenido | Copia metadata |
|---|---|---|
| `shutil.copy` | Sí | No |
| `shutil.copy2` | Sí | Sí |

Para sincronización es importante `copy2` — si el archivo en origen tiene fecha `2026-01-15`, el backup debe tener la misma fecha, no la fecha de la copia.

- `shutil.rmtree(ruta)` → Elimina un directorio y todo su contenido recursivamente. Equivalente a `rm -rf` en Unix.

```python
# limpiador.py
shutil.rmtree(ruta)    # Elimina __pycache__ y todo su contenido
```

**Por qué `rmtree` y no `ruta.rmdir()`:** `Path.rmdir()` solo elimina directorios vacíos. `shutil.rmtree()` elimina directorios con contenido — necesario para `__pycache__` que siempre tiene archivos dentro.

---

### argparse
**Qué es:** Módulo para construir interfaces de línea de comandos. Parsea `sys.argv`, valida argumentos, genera ayuda automáticamente y maneja errores de uso.

**Dónde se usa:** En `main.py`, función `construir_parser`.

**Conceptos utilizados:**

- `ArgumentParser` → Objeto principal del parser.

```python
# main.py
parser = argparse.ArgumentParser(
    prog="sincronizador",
    description="Sincronizador y limpiador de directorios CLI"
)
```

- `add_subparsers(dest, required)` → Crea un grupo de subcomandos. `dest` es el nombre del atributo donde se guarda el subcomando elegido. `required=True` hace que el subcomando sea obligatorio.

```python
# main.py
subparsers = parser.add_subparsers(dest="subcomando", required=True)
# args.subcomando → "sync", "clean" o "report"
```

- `subparsers.add_parser(nombre, help)` → Define un subcomando. Cada subcomando es un parser independiente con sus propios argumentos.

```python
# main.py
parser_sync = subparsers.add_parser("sync", help="Sincroniza origen → destino")
parser_clean = subparsers.add_parser("clean", help="Elimina archivos basura")
parser_report = subparsers.add_parser("report", help="Genera reporte de diferencias")
```

- `add_argument("--nombre", required, help)` → Define un argumento con nombre. `required=True` hace que sea obligatorio.

```python
# main.py
parser_sync.add_argument("--origen", required=True, help="Directorio fuente")
parser_sync.add_argument("--destino", required=True, help="Directorio destino")
```

- `add_argument("--flag", action="store_true")` → Define un flag booleano. Si el flag está presente en el comando, el atributo es `True`. Si no está, es `False`. No requiere valor.

```python
# main.py
parser_sync.add_argument("--dry-run", action="store_true")
# python main.py sync --dry-run → args.dry_run == True
# python main.py sync           → args.dry_run == False
```

**Nota sobre `--dry-run` y `args.dry_run`:** argparse convierte guiones en underscores automáticamente. `--dry-run` en la terminal se accede como `args.dry_run` en el código.

- `parser.parse_args()` → Parsea `sys.argv[1:]`, retorna objeto `Namespace` con los argumentos como atributos.

```python
# main.py
args = parser.parse_args()
# python main.py sync --origen ./a --destino ./b --dry-run
# → args.subcomando = "sync"
# → args.origen = "./a"
# → args.destino = "./b"
# → args.dry_run = True
```

**Generación automática de ayuda:** argparse construye el mensaje de `--help` automáticamente a partir de los `help=` de cada `add_argument`. No requiere código adicional.

---

### logging
**Qué es:** Módulo para registro de eventos con niveles de severidad. Alternativa estructurada a `print()` para aplicaciones que necesitan historial de operaciones.

**Niveles de severidad (de menor a mayor):**

| Nivel | Uso |
|---|---|
| `DEBUG` | Información detallada para diagnóstico |
| `INFO` | Operaciones normales del programa |
| `WARNING` | Situación inesperada pero no crítica |
| `ERROR` | Error que impide completar una operación |
| `CRITICAL` | Error que impide que el programa siga funcionando |

**Dónde se usa:** En todos los módulos — `logging.info()`, `logging.warning()`, `logging.error()` a lo largo del proyecto.

**Configuración centralizada:**

```python
# utilidades.py
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/operaciones.log", encoding="utf-8"),
        logging.StreamHandler()    # Salida a consola
    ]
)
```

**Dos handlers simultáneos:** `basicConfig` con lista de handlers permite escribir en archivo Y en consola al mismo tiempo. El `FileHandler` acumula log de todas las sesiones. El `StreamHandler` muestra el progreso en tiempo real.

**`logging` vs `print`:**

| | `print` | `logging` |
|---|---|---|
| Nivel de severidad | No | Sí |
| Timestamp automático | No | Sí |
| Escritura a archivo | Manual | Integrada |
| Filtrado por nivel | No | Sí |
| Desactivable sin borrar código | No | Sí |

---

### sys
**Qué es:** Módulo con acceso a variables y funciones del intérprete de Python.

**Dónde se usa:** En `main.py` para salida con código de error.

```python
# main.py
import sys
sys.exit(1)    # Termina el programa con código de salida 1 (error)
```

**Por qué `sys.exit(1)` y no solo `return`:** `sys.exit(1)` comunica al sistema operativo que el programa terminó con error. En scripts automatizados o pipelines, el código de salida permite detectar si el comando falló. `0` = éxito, cualquier otro número = error.

---

## Funciones Built-in

### sum() con generador
**Dónde se usa:** En `limpiador.py` y `reportes.py` para contar el total de elementos en el diccionario de basura.

```python
# limpiador.py
total = sum(len(v) for v in resultado.values())
# Suma la longitud de cada lista en el diccionario
# {"archivos_sistema": [a, b], "archivos_temporales": [c]} → 3
```

---

### open() en modo binario
**Dónde se usa:** En `utilidades.py` para leer archivos para hashing.

```python
# utilidades.py
with open(ruta, "rb") as f:    # "rb" = read binary
    bloque = f.read(8192)
```

**Por qué modo binario `"rb"` y no texto `"r"`:** El hash MD5 opera sobre bytes crudos. Abrir en modo texto haría que Python decodifique el contenido (aplicando conversión de saltos de línea y encoding), lo que alteraría los bytes y produciría hashes inconsistentes entre plataformas.

---

### any()
**Dónde se usa:** Implícito en el patrón `if not (hash_dest and hash_dest in hashes_origen)` en `comparador.py`.

---

## Tipos de Datos

### Conjuntos (set) como constantes de lookup
**Qué es:** Colección sin orden y sin duplicados. La pertenencia (`in`) es O(1) — tiempo constante independientemente del tamaño.

**Dónde se usa:** En `limpiador.py` para las listas de archivos y extensiones conocidas.

```python
# limpiador.py
ARCHIVOS_BASURA = {
    ".DS_Store", "Thumbs.db", "desktop.ini", ...
}

EXTENSIONES_TEMPORALES = {
    ".tmp", ".temp", ".bak", ".swp", ...
}

CARPETAS_BASURA = {
    "__pycache__", ".pytest_cache", "node_modules", ...
}

# Uso — O(1) en ambos casos
if ruta.name in ARCHIVOS_BASURA: ...
if ruta.suffix.lower() in EXTENSIONES_TEMPORALES: ...
```

**Por qué set y no lista:** `"archivo.tmp" in [".tmp", ".temp", ".bak"]` recorre la lista elemento por elemento — O(n). `"archivo.tmp" in {".tmp", ".temp", ".bak"}` usa una tabla hash interna — O(1). Para colecciones de nombres fijos que se consultan frecuentemente, set es la estructura correcta.

---

### Diccionario con listas como valores
**Patrón:** Diccionario que agrupa elementos por categoría. Cada clave mapea a una lista que crece durante el procesamiento.

```python
# comparador.py y limpiador.py
resultado = {
    "solo_en_origen": [],
    "solo_en_destino": [],
    "identicos": [],
    "modificados": [],
    "duplicados": []
}

# Acumulación durante el escaneo
resultado["identicos"].append(rel)
resultado["modificados"].append({"ruta": rel, ...})
```

**Por qué esta estructura:** Permite construir la clasificación en un solo recorrido y retornar todos los grupos en un solo objeto. El llamador accede a cada categoría por nombre de clave sin necesidad de múltiples retornos.

---

### Diccionario de grupos por hash
**Patrón:** Agrupar elementos por una propiedad calculada. Usado en `detectar_duplicados_internos`.

```python
# comparador.py
grupos_hash = {}
for rel, abs_path in archivos.items():
    h = hash_archivo(abs_path)
    if h:
        if h not in grupos_hash:
            grupos_hash[h] = []
        grupos_hash[h].append(rel)

# Filtrar solo los grupos con más de un archivo
duplicados = {
    h: rutas for h, rutas in grupos_hash.items()
    if len(rutas) > 1
}
```

Este patrón — construir un diccionario de listas agrupadas por clave calculada — aparece frecuentemente en procesamiento de datos.

---

## Estructuras de Control

### Walrus operator `:=` (Python 3.8+)
**Qué es:** Operador de asignación dentro de expresiones. Asigna y evalúa en la misma operación.

**Dónde se usa:** En `utilidades.py` dentro del loop de lectura de archivos.

```python
# utilidades.py
while bloque := f.read(8192):
    hasher.update(bloque)
```

**Equivalencia sin walrus:**
```python
# Sin walrus operator
while True:
    bloque = f.read(8192)
    if not bloque:
        break
    hasher.update(bloque)
```

`f.read(8192)` retorna un bytes vacío `b""` al llegar al fin del archivo. En Python, `b""` es falso — el walrus operator asigna el resultado y lo evalúa como condición del `while` en una sola expresión. Es más conciso y elimina la necesidad del `break` explícito.

**Por qué es Python 3.8+:** El walrus operator fue introducido en Python 3.8 (PEP 572). En versiones anteriores se necesita el patrón con `while True` y `break`.

---

### Dict comprehension con filtro
**Dónde se usa:** En `comparador.py` para filtrar grupos de duplicados.

```python
# comparador.py
duplicados = {
    h: rutas for h, rutas in grupos_hash.items()
    if len(rutas) > 1
}
```

Equivalente a:
```python
duplicados = {}
for h, rutas in grupos_hash.items():
    if len(rutas) > 1:
        duplicados[h] = rutas
```

---

### Iteración sobre `.items()` de diccionario
**Qué es:** Método que retorna pares (clave, valor) para iterar sobre ambos simultáneamente.

**Dónde se usa:** En `comparador.py` y `reportes.py` extensivamente.

```python
# comparador.py
for rel, abs_path in archivos_origen.items():
    # rel = ruta relativa (string)
    # abs_path = ruta absoluta (Path)
```

```python
# reportes.py
for clave, nombre in categorias.items():
    # clave = "archivos_sistema"
    # nombre = "Archivos del sistema"
```

---

## Patrones de Diseño Aplicados

### Subcomandos CLI con argparse
**Patrón:** Interfaz CLI con múltiples subcomandos donde cada uno tiene sus propios flags. Es el patrón que usan `git`, `docker`, `pip` y la mayoría de herramientas CLI profesionales.

```bash
git commit --message "texto"    # subcomando: commit, flag: --message
git push --force                # subcomando: push, flag: --force
python main.py sync --dry-run   # subcomando: sync, flag: --dry-run
```

**Implementación:**
```python
# main.py
subparsers = parser.add_subparsers(dest="subcomando", required=True)
parser_sync = subparsers.add_parser("sync")
parser_sync.add_argument("--dry-run", action="store_true")
```

Cada subparser es independiente — `--dry-run` en `sync` no afecta a `report`, que ni siquiera tiene ese flag.

---

### Modo dry-run para operaciones destructivas
**Patrón:** Flag `--dry-run` que simula la operación registrando en log lo que haría sin ejecutar ningún cambio en disco.

```python
# sincronizador.py
def sincronizar(origen, destino, dry_run=False):
    modo = "[DRY-RUN] " if dry_run else ""
    ...
    logging.info(f"{modo}COPIAR: {rel}")
    if not dry_run:
        shutil.copy2(src, dst)    # Solo ejecuta si no es dry-run
        operaciones["copiados"] += 1
    else:
        operaciones["copiados"] += 1    # Cuenta igual para el reporte
```

El contador se incrementa en ambos casos — el reporte final muestra cuántas operaciones se ejecutarían, no cuántas se ejecutaron.

**Por qué es crítico para operaciones de archivo:** Mover o eliminar archivos es irreversible. El dry-run permite verificar el comportamiento antes de comprometerse con la operación.

---

### Logging transversal sin acoplamiento
**Patrón:** Cada módulo usa `logging.info()`, `logging.warning()`, `logging.error()` directamente, sin importar el logger ni el handler. La configuración centralizada en `configurar_logging()` establece dónde y cómo se escribe todo.

```python
# comparador.py — usa logging sin saber a dónde va
logging.info(f"Comparando: {origen} ↔ {destino}")

# limpiador.py — igual
logging.warning(f"No se pudo eliminar {ruta}")

# La configuración está en un solo lugar:
# utilidades.py → configurar_logging() → FileHandler + StreamHandler
```

**Ventaja:** Si se quisiera cambiar el destino del log (ej: enviar a un servidor remoto), solo se modifica `configurar_logging()` — ningún otro módulo cambia.

---

### Separación escaneo/ejecución
**Patrón:** Las funciones de escaneo (`escanear_basura`, `comparar_directorios`) retornan datos sin ejecutar operaciones. Las funciones de ejecución (`limpiar`, `sincronizar`) reciben esos datos y actúan.

```python
# Escaneo — solo lee, no modifica
basura = escanear_basura(carpeta)      # retorna dict de rutas

# Reporte — usa el escaneo para mostrar
print(reporte_limpieza(carpeta))       # llama escanear internamente

# Ejecución — usa el escaneo para actuar
limpiar(carpeta, dry_run=False)        # llama escanear y luego elimina
```

**Ventaja:** Permite mostrar el reporte antes de ejecutar la limpieza — el usuario ve exactamente qué se va a eliminar antes de confirmar.