from pathlib import Path
import os
import re
import pandas as pd

# ============================================================
# CONFIGURACIÓN
# ============================================================
# Si tienes config.py con RUTA_DATOS, CUERPO y ESPECIALIDAD, lo usa.
# Si no existe, usa la carpeta donde está este script.
try:
    from config import *  # noqa
except ImportError:
    RUTA_DATOS = "."
    CUERPO = "MAESTROS"
    ESPECIALIDAD = "AL"

CARPETA = Path(RUTA_DATOS).resolve()
CARPETA_XLSX = CARPETA / "xlsx"
CARPETA_XLSX.mkdir(parents=True, exist_ok=True)

TXT = CARPETA / "TODOS_LOS_TXT_UNIDOS.txt"
EXCEL = CARPETA_XLSX / f"{CUERPO}-{ESPECIALIDAD}_notas_segunda_prueba.xlsx"
DEBUG = CARPETA / "LINEAS_RECONSTRUIDAS.txt"

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def normalizar(linea: str) -> str:
    """Quita espacios duplicados y caracteres raros manteniendo acentos."""
    return " ".join(linea.replace("\ufeff", "").split())


def es_inicio_cabecera_o_pie(linea: str) -> bool:
    """Detecta líneas que no forman parte del registro de un opositor."""
    patrones = [
        r"^=+$",
        r"^FICHERO:",
        r"^CALIFICACIONES",
        r"^PROCESO SELECTIVO",
        r"^ESPECIALIDAD\s+",
        r"^Desde\s+",
        r"^Orden\s+Acceso",
        r"^VºBº",
        r"^Fdo\.",
        r"^\d{2}/\d{2}/\d{4}\s+-\s+\d{2}:\d{2}:\d{2}\s+Página",
    ]
    return any(re.search(p, linea, re.IGNORECASE) for p in patrones)


# Formato esperado en el TXT adjunto:
# 00400 1 ***8381** - VICENTE SANCHEZ, SOFIA 9,2900
PATRON_OPOSITOR = re.compile(
    r"""
    ^
    (?P<orden>\d+)\s+
    (?P<acceso>\d+)\s+
    (?P<dni>\*{3}\d+\*{2})
    \s*-\s*
    (?P<nombre>.+?)
    \s+
    (?P<puntuacion>\d+,\d+|NP|--|-)
    $
    """,
    re.VERBOSE,
)


def reconstruir_lineas(lineas):
    """
    Reconstruye registros que hayan podido partirse en varias líneas.
    Solo une líneas cuando empieza un opositor y todavía no cumple el patrón completo.
    """
    salida = []
    i = 0

    while i < len(lineas):
        linea = normalizar(lineas[i])

        if not linea:
            i += 1
            continue

        # Si ya es una línea de opositor completa, se guarda tal cual.
        if PATRON_OPOSITOR.match(linea):
            salida.append(linea)
            i += 1
            continue

        # Si empieza como registro de opositor pero no está completo, intenta unir siguientes líneas.
        if re.match(r"^\d+\s+\d+\s+\*{3}\d+\*{2}\s*-", linea):
            reconstruida = linea
            j = i + 1

            while j < len(lineas):
                siguiente = normalizar(lineas[j])

                if not siguiente:
                    j += 1
                    continue

                if es_inicio_cabecera_o_pie(siguiente):
                    break

                reconstruida = normalizar(reconstruida + " " + siguiente)

                if PATRON_OPOSITOR.match(reconstruida):
                    break

                j += 1

            salida.append(reconstruida)
            i = max(j + 1, i + 1)
            continue

        salida.append(linea)
        i += 1

    return salida


def convertir_nota(valor):
    if valor in {"NP", "--", "-", None}:
        return None
    return float(valor.replace(",", "."))


def resultado(nota):
    if pd.isna(nota):
        return "NP"
    return "APROBADO" if nota >= 5 else "SUSPENSO"


# ============================================================
# LECTURA TXT
# ============================================================

print("=" * 80)
print("TXT_A_EXCEL - NOTAS OPOSITORES")
print("=" * 80)
print("TXT =", TXT)
print("EXISTE TXT =", TXT.exists())
print("EXCEL =", EXCEL)
print("=" * 80)

if not TXT.exists():
    raise FileNotFoundError(f"No existe el fichero: {TXT}")

with open(TXT, "r", encoding="utf-8", errors="ignore") as f:
    lineas_originales = f.readlines()

lineas = reconstruir_lineas(lineas_originales)

with open(DEBUG, "w", encoding="utf-8") as f:
    for linea in lineas:
        f.write(linea + "\n")

print("Líneas reconstruidas:", len(lineas))
print("Debug generado:", DEBUG)

# ============================================================
# PARSEO
# ============================================================

registros = []
lineas_no_parseadas = []

fichero_actual = None
especialidad_actual = None
tribunal_actual = None
fecha_desde_actual = None
fecha_hasta_actual = None
estoy_en_tabla = False

for linea in lineas:
    linea = normalizar(linea)

    if not linea:
        continue

    mfichero = re.search(r"^FICHERO:\s*(.+)$", linea, re.IGNORECASE)
    if mfichero:
        fichero_actual = mfichero.group(1).strip()
        estoy_en_tabla = False
        continue

    mesp = re.search(
        r"^ESPECIALIDAD\s+(.+?)\s*-\s*TRIBUNAL\s*N[º°]?\s*(\d+)",
        linea,
        re.IGNORECASE,
    )
    if mesp:
        especialidad_actual = mesp.group(1).strip()
        tribunal_actual = int(mesp.group(2))
        estoy_en_tabla = False
        continue

    mfechas = re.search(
        r"Desde\s+(\d{2}/\d{2}/\d{4})\s+Hasta\s+(\d{2}/\d{2}/\d{4})",
        linea,
        re.IGNORECASE,
    )
    if mfechas:
        fecha_desde_actual = mfechas.group(1)
        fecha_hasta_actual = mfechas.group(2)
        continue

    if re.search(r"^Orden\s+Acceso\s+Opositor\s+Puntuaci[oó]n", linea, re.IGNORECASE):
        estoy_en_tabla = True
        continue

    if estoy_en_tabla and es_inicio_cabecera_o_pie(linea):
        estoy_en_tabla = False
        continue

    m = PATRON_OPOSITOR.match(linea)

    if m:
        nota = convertir_nota(m.group("puntuacion"))

        registros.append(
            {
                "Fichero": fichero_actual,
                "Especialidad": especialidad_actual,
                "Tribunal": tribunal_actual,
                "Fecha Desde": fecha_desde_actual,
                "Fecha Hasta": fecha_hasta_actual,
                "Orden": m.group("orden"),
                "Acceso": m.group("acceso"),
                "Identificador": m.group("dni"),
                "Opositor": m.group("nombre").strip(),
                "Puntuación": nota,
                "Resultado": resultado(nota),
            }
        )
        continue

    # Si estamos dentro de la tabla y hay algo que parece dato, lo guardamos para revisar.
    if estoy_en_tabla and re.search(r"\*{3}\d+\*{2}|^\d+\s+\d+", linea):
        lineas_no_parseadas.append(
            {
                "Fichero": fichero_actual,
                "Tribunal": tribunal_actual,
                "Linea": linea,
            }
        )

# ============================================================
# DATAFRAME + RANKINGS
# ============================================================

df = pd.DataFrame(registros)

print("Registros encontrados:", len(df))

if df.empty:
    print("NO SE HA EXTRAÍDO NINGÚN REGISTRO")
    if lineas_no_parseadas:
        print("Líneas candidatas no parseadas:", len(lineas_no_parseadas))
    raise SystemExit(1)

# Ranking global: mayor puntuación = ranking 1.
df["Ranking Global"] = df["Puntuación"].rank(method="min", ascending=False, na_option="bottom").astype("Int64")

# Ranking por tribunal.
df["Ranking Tribunal"] = (
    df.groupby("Tribunal")["Puntuación"]
    .rank(method="min", ascending=False, na_option="bottom")
    .astype("Int64")
)

# Orden estable para exportación.
df = df.sort_values(["Tribunal", "Orden"], na_position="last")

resumen_tribunal = (
    df.groupby(["Especialidad", "Tribunal"], dropna=False)
    .agg(
        Opositores=("Opositor", "count"),
        Aprobados=("Resultado", lambda s: (s == "APROBADO").sum()),
        Suspensos=("Resultado", lambda s: (s == "SUSPENSO").sum()),
        NP=("Resultado", lambda s: (s == "NP").sum()),
        Nota_Media=("Puntuación", "mean"),
        Nota_Maxima=("Puntuación", "max"),
        Nota_Minima=("Puntuación", "min"),
    )
    .reset_index()
)

resumen_total = pd.DataFrame(
    {
        "Opositores": [len(df)],
        "Aprobados": [(df["Resultado"] == "APROBADO").sum()],
        "Suspensos": [(df["Resultado"] == "SUSPENSO").sum()],
        "NP": [(df["Resultado"] == "NP").sum()],
        "Nota Media": [df["Puntuación"].mean()],
        "Nota Máxima": [df["Puntuación"].max()],
        "Nota Mínima": [df["Puntuación"].min()],
    }
)

no_parseadas_df = pd.DataFrame(lineas_no_parseadas)

# ============================================================
# EXPORTAR EXCEL
# ============================================================

if os.path.exists(EXCEL):
    try:
        os.remove(EXCEL)
    except PermissionError:
        print()
        print("CIERRA EL EXCEL antes de ejecutar de nuevo:")
        print(EXCEL)
        raise SystemExit(1)

with pd.ExcelWriter(EXCEL, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Notas", index=False)
    resumen_tribunal.to_excel(writer, sheet_name="Resumen Tribunal", index=False)
    resumen_total.to_excel(writer, sheet_name="Resumen Total", index=False)

    if not no_parseadas_df.empty:
        no_parseadas_df.to_excel(writer, sheet_name="No parseadas", index=False)

    # Ajuste básico de anchos y filtros.
    for sheet_name, worksheet in writer.sheets.items():
        worksheet.auto_filter.ref = worksheet.dimensions
        worksheet.freeze_panes = "A2"

        for column_cells in worksheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                value = cell.value
                if value is not None:
                    max_length = max(max_length, len(str(value)))

            worksheet.column_dimensions[column_letter].width = min(max_length + 2, 45)

print()
print("Excel generado:")
print(EXCEL)
print("Filas exportadas:", len(df))
print("Líneas no parseadas:", len(no_parseadas_df))
