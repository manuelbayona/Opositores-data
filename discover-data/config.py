import os
from pathlib import Path

# ============================================================
# BASE
# ============================================================

BASE_DIR = Path(
    r"C:\Users\JI53BQ\OneDrive - ING\Desktop\tribunales\segunda_prueba"
)

# ============================================================
# CUERPO
# ============================================================

CUERPO = "0597"

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

NOMBRE_DOCUMENTO = (
    "Calificaciones segunda prueba"
)

PDF_TEXTO_EXACTO = (
    "CALIFICACIONES DE OPOSITORES SEGUNDA PRUEBA"
)

# ============================================================
# TRIBUNALES
# ============================================================

TRIBUNAL_DESDE = 1
TRIBUNAL_HASTA = 50

# ============================================================
# RUTAS
# ============================================================

RUTA_DATOS = (
    BASE_DIR /
    f"{CUERPO}-{ESPECIALIDAD}"
)

print("=" * 80)
print("CONFIG ACTIVA")
print("=" * 80)
print("CUERPO      =", CUERPO)
print("ESPECIALIDAD=", ESPECIALIDAD)
print("RUTA_DATOS  =", RUTA_DATOS)
print("=" * 80)