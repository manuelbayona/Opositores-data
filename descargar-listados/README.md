# Descargar listados de interés

Descarga únicamente los PDFs de resultados publicados por tribunal —calificaciones
de primera/segunda prueba, puntuaciones (provisionales/definitivas), listados de
baremación (méritos), aprobados en fase de oposición— filtrando por el título real
que el propio portal le da a cada publicación. Ignora citaciones, plazos de
alegaciones y demás documentos puramente administrativos.

Es una versión aparte de `discover-data/descargar_listados.py` (mismo contenido),
pensada para poder ejecutarse y probarse de forma aislada sin depender del resto del
pipeline (`extraer_notas.py`, `txt_a_excel.py`, etc.).

## Cómo obtener esta rama

Todavía no está en `main` — está en la rama `feature/descargar-listados-interes`,
pendiente de que la pruebes tú antes de abrir la PR:

```bash
git fetch origin feature/descargar-listados-interes
git checkout feature/descargar-listados-interes
cd descargar-listados
```

PR (aún no abierta):
https://github.com/manuelbayona/Opositores-data/pull/new/feature/descargar-listados-interes

## Instalación

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (CMD):**

```bat
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

(`py` es el lanzador de Python en Windows; si no está disponible usa `python` en su
lugar. Tras `activate.bat` el prompt debe mostrar `(.venv)` delante de la ruta.)

## Configuración

Todo lo configurable vive en `config.py`, sobreescribible por variable de entorno —
no hace falta editar ningún fichero para probar con otra convocatoria/especialidad:

| Variable | Por defecto | Qué es |
|---|---|---|
| `ANYO` | `2026` | Año de la convocatoria en Educarm |
| `CONVOCATORIA` | `OPOPRI26` | Código de convocatoria en Educarm |
| `CUERPO` | `0597` | Código de cuerpo (0597 = Maestros) |
| `ESPECIALIDAD` | `EI` | Especialidad a consultar (ver `ESPECIALIDADES` en `config.py` para los códigos) |
| `TRIBUNAL_DESDE` / `TRIBUNAL_HASTA` | `1` / `50` | Solo se usa como respaldo si el descubrimiento automático de tribunales no encuentra ninguno |
| `PALABRAS_CLAVE_INTERES` | `calificaciones,puntuaciones,baremacion,merito,aprobados,seleccionados` | Un PDF se descarga si su nombre o su título contiene alguna de estas palabras (sin tildes/mayúsculas) |
| `PALABRAS_CLAVE_EXCLUIR` | `citacion,plazo de presentacion,resolucion provisional,apertura de cabeceras` | Veto sobre lo anterior — descarta citaciones administrativas aunque mencionen de pasada una palabra de interés |
| `BASE_DIR` | `./descargas` (junto a este script) | Carpeta raíz donde se guarda todo |
| `EDUCARM_COOKIE` | (vacío) | Normalmente innecesario — ver más abajo |

## Ejecutar

**Linux / macOS:**

Una sola especialidad/convocatoria (la que esté configurada, por defecto EI /
OPOPRI26 / 2026):

```bash
python3 descargar_listados.py
```

Otra especialidad sin tocar el código:

```bash
ESPECIALIDAD=PRI python3 descargar_listados.py
```

Todas las especialidades de las convocatorias listadas en
`orquestador_descargas.py` (edítalo para añadir más convocatorias):

```bash
python3 orquestador_descargas.py
```

**Windows (CMD):**

Con el entorno virtual activado (`.venv\Scripts\activate.bat`), una sola
especialidad/convocatoria (por defecto EI / OPOPRI26 / 2026):

```bat
python descargar_listados.py
```

Otra especialidad sin tocar el código — en `cmd.exe` las variables de entorno se
fijan con `set` en una línea aparte, no delante del comando como en Linux:

```bat
set ESPECIALIDAD=PRI
python descargar_listados.py
```

(Ese `set` deja `ESPECIALIDAD` fijada para el resto de la sesión de CMD. Para
volver al valor por defecto, cierra y abre una ventana nueva, o `set ESPECIALIDAD=`
para vaciarla.)

Todas las especialidades de las convocatorias listadas en
`orquestador_descargas.py`:

```bat
python orquestador_descargas.py
```

## Dónde queda todo

```
descargas/
  <ANYO>-<CONVOCATORIA>/
    <CUERPO>-<ESPECIALIDAD>/
      html/            # respuesta completa de cada tribunal consultado (para depurar)
      pdf/              # solo los PDFs que pasaron el filtro de interés
    xlsx/
      <ANYO>-<CONVOCATORIA>_resultados.xlsx   # generado por extraer_resultados.py
```

Si el descubrimiento automático de tribunales no encuentra ninguno para una
especialidad, se guarda la respuesta cruda en
`html/debug_ajaxOpcionesTribunal_<especialidad>.html` para poder revisar por qué.

## Extraer los datos de los PDFs a Excel

Una vez descargados los PDFs de una convocatoria (todas sus especialidades),
`extraer_resultados.py` los recorre todos y genera un único Excel con los datos ya
estructurados:

```bash
ANYO=2024 CONVOCATORIA=OPOPRI24 python3 extraer_resultados.py
```

Reconoce el PDF por su contenido (no por el nombre de fichero) y lo manda a una de
dos familias:

- **Puntuaciones**: calificaciones/puntuaciones de cualquier prueba (columnas
  `Orden`, `Acceso`, `Identificador`, `Opositor`, `Parte A`/`Parte B` cuando la
  prueba las tiene, `Puntuación`).
- **Baremación**: listado de méritos (columnas `T.Ap.1`, `T.Ap.2`, `T.Ap.3`,
  `Baremo`, `Ap.1.1`...`Ap.3.7` — leídas de la propia cabecera del PDF, no fijas en
  el código, porque cambian según el tipo de acceso).

Cada tribunal republica el mismo listado varias veces (correcciones, provisional →
definitivo). No se descarta ninguna versión — el Excel trae una hoja con **todas**
las versiones y otra solo con la **última** (`Es_Ultima_Version=True`, la de fecha
más reciente por especialidad+tribunal+tipo de publicación) para trabajar
directamente con esa sin tener que filtrar a mano.

Si alguna fila no se puede interpretar con confianza (formato distinto al
esperado), se guarda igualmente pero con la columna `Valores sin interpretar`
rellena en vez de rellenar el resto de columnas con un valor adivinado — así se
puede revisar a mano sin que se cuele un dato incorrecto en el resto de la hoja.
Los PDFs sin ninguna de las dos cabeceras reconocidas (p.ej. un aviso de trámite que
coló el filtro de descarga) se listan al final por consola como
"FORMATO NO RECONOCIDO", sin frenar el resto del proceso.

## Aviso importante: el portal puede bloquear la petición

Esto llama directamente a un endpoint real de Educarm
(`servicios.educarm.es/admin/index2.php`). Ese portal tiene protección anti-bot
(WAF de Radware) que en nuestras pruebas **bloqueó las peticiones hechas con
`curl`/`requests` desde un entorno de servidor/sandbox** (403, cabecera
`server: rdwr`), pero **sí dejó pasar la misma petición exacta capturada desde un
navegador real** (200, cabecera `rdwr_response: allowed`) — no es un problema de
cookies ni de sesión, es huella de navegador (TLS/HTTP2), y no hay forma de
solucionarlo desde este script sin intentar sortear esa protección, cosa que
deliberadamente no se ha hecho aquí.

En la práctica: pruébalo primero tú, desde tu propio ordenador/red normal. Si te
devuelve 403 en vez de descargar nada, es ese bloqueo — no un bug del script.

## Fuente de esta lógica

El flujo (descubrir tribunales → pedir publicaciones → filtrar por título) y el
patrón exacto de los enlaces de descarga están verificados contra capturas reales
del portal en `../2026-murcia-maestros/requests/` (`response4.har` en particular,
que trae el HTML completo de una respuesta real de `getPublicaciones`).
