import os
from pathlib import Path

# ============================================================
# BASE
# ============================================================
# Portable by default (relative to this repo, next to discover-data/) instead of a
# hardcoded per-machine path. Override with BASE_DIR to keep downloads elsewhere.

BASE_DIR = Path(
    os.getenv(
        "BASE_DIR",
        str(Path(__file__).resolve().parent.parent / "descargas"),
    )
)

# ============================================================
# CONVOCATORIA
# ============================================================
# The two query params Educarm's publicacionesTribunales endpoint actually needs to
# scope a query to one convocatoria. Previously hardcoded directly in tribunales.py's
# BASE_URL — now a single place to change them for a different convocatoria/year.

ANYO = os.getenv("ANYO", "2026")
CONVOCATORIA = os.getenv("CONVOCATORIA", "OPOPRI26")

# ============================================================
# CUERPO
# ============================================================

CUERPO = os.getenv("CUERPO", "0597")

# ============================================================
# ESPECIALIDAD
# ============================================================

ESPECIALIDAD = os.getenv(
    "ESPECIALIDAD",
    "EI"
)

# ============================================================
# ESPECIALIDADES
# ============================================================

ESPECIALIDADES = {
    "AL": "AUDICION Y LENGUAJE",
    "EF": "EDUCACION FISICA",
    "EI": "EDUCACION INFANTIL",
    "FF": "LENGUA EXTRANJERA: FRANCES",
    "FI": "LENGUA EXT.: INGLES (MAESTROS PRIMARIA)",
    "MU": "MUSICA",
    "PRI": "EDUCACION PRIMARIA",
    "PT": "PEDAGOGIA TERAPEUTICA",
}

# ============================================================
# EDUCARM
# ============================================================
# Also overridable, so a convocatoria whose "prueba" of interest isn't the second one
# (or with a differently-worded header) doesn't require editing this file by hand.

NOMBRE_DOCUMENTO = os.getenv(
    "NOMBRE_DOCUMENTO",
    "Calificaciones segunda prueba",
)

PDF_TEXTO_EXACTO = os.getenv(
    "PDF_TEXTO_EXACTO",
    "CALIFICACIONES DE OPOSITORES SEGUNDA PRUEBA",
)

# ============================================================
# LISTADOS DE INTERÉS
# ============================================================
# Cada publicación real trae un título legible (ver response4.har: "Calificaciones
# segunda prueba", "Puntuaciones obtenidas fase oposición", "Listado baremación -
# Acceso 1"...) frente a ruido puramente administrativo ("CITACIÓN A DETERMINADOS
# ASPIRANTES", "PLAZO DE PRESENTACIÓN DE RECLAMACIONES...", "RESOLUCIÓN
# PROVISIONAL..."). Solo se descarga un PDF si su nombre de fichero o ese título
# contiene alguna de estas palabras (sin distinguir mayúsculas/tildes). Lista aparte
# y fácil de tocar porque el vocabulario exacto puede variar entre convocatorias.

PALABRAS_CLAVE_INTERES = os.getenv(
    "PALABRAS_CLAVE_INTERES",
    "calificaciones,puntuaciones,baremacion,merito,aprobados,seleccionados",
).split(",")

# Veto sobre lo anterior: un documento que coincida con una palabra de interés pero
# también con una de estas se descarta igualmente. Necesario porque una citación
# puramente administrativa puede mencionar la palabra sin ser un listado — ejemplo
# real: "CITACIÓN ENTREGA DE PROGRAMACIONES Y FICHA DE MÉRITOS" contiene "méritos"
# pero es una citación de trámite, no el listado de méritos en sí.
PALABRAS_CLAVE_EXCLUIR = os.getenv(
    "PALABRAS_CLAVE_EXCLUIR",
    "citacion,plazo de presentacion,resolucion provisional,apertura de cabeceras",
).split(",")

# ============================================================
# TRIBUNALES
# ============================================================

TRIBUNAL_DESDE = int(os.getenv("TRIBUNAL_DESDE", "1"))
TRIBUNAL_HASTA = int(os.getenv("TRIBUNAL_HASTA", "50"))

# ============================================================
# RUTAS
# ============================================================
# One folder per convocatoria (ANYO-CONVOCATORIA), then per especialidad within it, so
# downloads from different convocatorias never collide or overwrite each other.

RUTA_DATOS = (
    BASE_DIR /
    f"{ANYO}-{CONVOCATORIA}" /
    f"{CUERPO}-{ESPECIALIDAD}"
)

print("=" * 80)
print("CONFIG ACTIVA")
print("=" * 80)
print("ANYO        =", ANYO)
print("CONVOCATORIA=", CONVOCATORIA)
print("CUERPO      =", CUERPO)
print("ESPECIALIDAD=", ESPECIALIDAD)
print("RUTA_DATOS  =", RUTA_DATOS)
print("=" * 80)
