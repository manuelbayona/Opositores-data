"""
Extrae datos estructurados de los PDFs ya descargados por descargar_listados.py, para
todas las especialidades de una convocatoria.

A diferencia de discover-data/extraer_notas.py + txt_a_excel.py (pensados solo para
el formato "Orden Acceso Opositor Puntuación" de las calificaciones de segunda
prueba), este script reconoce y extrae las DOS familias reales de tabla que hay en
los PDFs descargados:

  - "puntuaciones": calificaciones/puntuaciones por prueba (segunda prueba, primera
    prueba con Parte A/Parte B, fase de oposición). Cabecera real: "Orden Acceso
    Opositor Puntuación" o "Orden Acceso Opositor (Máx. ...) (Máx. ...) (Máx. ...)".
  - "baremacion": listado de baremación (méritos), con muchas más columnas
    (T.Ap.1/2/3, Baremo, Ap.1.1..Ap.3.7) que además varían de una convocatoria a
    otra. Cabecera real: "Apellidos y Nombre S N.I.F. Ac T.Ap.1 ...".

La familia se detecta por el CONTENIDO del PDF (qué cabecera aparece), no por el
nombre de fichero, así no depende de que el nombre siga siempre el mismo patrón.
Las columnas de baremación se leen también del propio PDF (todo lo que hay entre
"Ac" y el final de la cabecera), en vez de darlas por sabidas, porque ese listado de
columnas cambia según el tipo de acceso.

Cada tribunal republica el mismo tipo de listado varias veces (correcciones,
provisional -> definitivo...). No se descarta ninguna versión: se extraen todas y se
marca con Es_Ultima_Version=True solo la de fecha/hora más reciente por
(especialidad, tribunal, tipo de publicación), para no perder trazabilidad con el
original (ver CLAUDE.md del extractor, "preservación de datos crudos").
"""

import glob
import os
import re
import sys

import pandas as pd
import pdfplumber

from config import *

# ============================================================
# CLASIFICACIÓN DE FICHERO POR NOMBRE
# ============================================================
# 0597AL01_listado_baremacion_acceso_1_07091016.pdf
#   cuerpo=0597 especialidad=AL tribunal=01 tipo=listado_baremacion_acceso_1 marca_tiempo=07091016
NOMBRE_RE = re.compile(
    r"^(?P<cuerpo>\d{4})(?P<especialidad>[A-Z]+)(?P<tribunal>\d{2})_"
    r"(?P<tipo>.+)_(?P<marca_tiempo>\d{8,10})$"
)

# ============================================================
# FAMILIA "PUNTUACIONES"
# ============================================================
# Una fila válida siempre empieza por orden/acceso/dni enmascarado y termina en 1 o 3
# valores (Puntuación sola, o Parte A / Parte B / Puntuación) que pueden ser NP/--/-.
FILA_PUNTUACIONES_RE = re.compile(
    r"^(?P<orden>\d+)\s+"
    r"(?P<acceso>\d+)\s+"
    r"(?P<dni>\*{3}\d+\*{2})\s*-\s*"
    r"(?P<nombre>.+?)\s+"
    r"(?P<valores>(?:\d+,\d+|NP|--|-)(?:\s+(?:\d+,\d+|NP|--|-))*)$"
)

# ============================================================
# FAMILIA "BAREMACION"
# ============================================================
CABECERA_BAREMACION_RE = re.compile(r"^Apellidos y Nombre\b.*$")
FILA_BAREMACION_RE = re.compile(
    r"^(?P<nombre>.+?)\s+"
    r"(?P<dni>\*{3}\d+\*{2})\s+"
    r"(?P<ac>\d+)\s+"
    r"(?P<valores>[\d,]+(?:\s+[\d,]+)*)$"
)
ACCESO_LINEA_RE = re.compile(r"^Acceso:\s*(.+)$")

# Todos los valores de baremación llevan siempre 4 decimales (p.ej. "10,6749"). Cuando
# dos columnas quedan pegadas sin espacio en el texto extraído del PDF (columnas muy
# próximas en la tabla original, p.ej. "0,750010,6749"), separar por longitud fija de
# decimales reconstruye los valores reales en vez de perderlos como una sola cadena
# sin interpretar.
VALOR_BAREMACION_RE = re.compile(r"\d+,\d{4}")


def columnas_baremacion(cabecera: str) -> list[str]:
    """De 'Apellidos y Nombre S N.I.F. Ac T.Ap.1 T.Ap.2 ...' se queda con lo que hay
    después de 'Ac' (los nombres reales de las columnas numéricas de ese PDF)."""

    tokens = cabecera.split()

    if "Ac" not in tokens:
        return []

    return tokens[tokens.index("Ac") + 1:]


def convertir_valor(valor: str):
    if valor in {"NP", "--", "-"}:
        return None
    return float(valor.replace(",", "."))


def texto_completo(ruta_pdf: str) -> str:
    with pdfplumber.open(ruta_pdf) as pdf:
        paginas = [pagina.extract_text() or "" for pagina in pdf.pages]
    return "\n".join(paginas)


def parsear_puntuaciones(texto: str) -> list[dict]:
    filas = []

    for linea in texto.splitlines():
        m = FILA_PUNTUACIONES_RE.match(linea.strip())

        if not m:
            continue

        valores = m.group("valores").split()

        if len(valores) == 1:
            parte_a, parte_b, puntuacion = None, None, valores[0]
        elif len(valores) == 3:
            parte_a, parte_b, puntuacion = valores
        else:
            # Forma no vista hasta ahora: no adivinar qué es cada valor, guardar tal
            # cual para revisión en vez de asignarlo mal.
            parte_a, parte_b, puntuacion = None, None, None

        filas.append(
            {
                "Orden": int(m.group("orden")),
                "Acceso": int(m.group("acceso")),
                "Identificador": m.group("dni"),
                "Opositor": m.group("nombre").strip(),
                "Parte A": convertir_valor(parte_a) if parte_a else None,
                "Parte B": convertir_valor(parte_b) if parte_b else None,
                "Puntuación": convertir_valor(puntuacion) if puntuacion else None,
                "Valores sin interpretar": (
                    m.group("valores") if puntuacion is None else None
                ),
            }
        )

    return filas


def parsear_baremacion(texto: str) -> list[dict]:
    filas = []
    columnas: list[str] = []
    acceso_declarado = None

    for linea in texto.splitlines():
        linea = linea.strip()

        if not linea:
            continue

        macceso = ACCESO_LINEA_RE.match(linea)
        if macceso:
            acceso_declarado = macceso.group(1).strip()
            continue

        if CABECERA_BAREMACION_RE.match(linea):
            columnas = columnas_baremacion(linea)
            continue

        if not columnas:
            # Todavía no hemos visto la cabecera de este PDF: no hay con qué
            # interpretar los valores numéricos de una fila.
            continue

        m = FILA_BAREMACION_RE.match(linea)

        if not m:
            continue

        valores = VALOR_BAREMACION_RE.findall(m.group("valores"))

        fila = {
            "Opositor": m.group("nombre").strip(),
            "Identificador": m.group("dni"),
            "Acceso (código)": int(m.group("ac")),
            "Acceso declarado": acceso_declarado,
        }

        if len(valores) == len(columnas):
            for nombre_columna, valor in zip(columnas, valores):
                fila[nombre_columna] = convertir_valor(valor)
        else:
            # Número de valores distinto al de columnas de la cabecera: no repartir
            # a ciegas, dejar constancia para revisar el PDF concreto.
            fila["Valores sin interpretar"] = m.group("valores")

        filas.append(fila)

    return filas


def procesar_pdf(ruta_pdf: str, metadatos_fichero: dict) -> tuple[list[dict], list[dict], str]:
    try:
        texto = texto_completo(ruta_pdf)
    except Exception as e:
        print(f"    ERROR LEYENDO PDF: {e}")
        return [], [], "error_lectura"

    es_baremacion = "Apellidos y Nombre" in texto
    es_puntuaciones = "Orden Acceso Opositor" in texto

    if es_baremacion:
        filas = parsear_baremacion(texto)
        for fila in filas:
            fila.update(metadatos_fichero)
        return [], filas, "baremacion"

    if es_puntuaciones:
        filas = parsear_puntuaciones(texto)
        for fila in filas:
            fila.update(metadatos_fichero)
        return filas, [], "puntuaciones"

    print("    FORMATO NO RECONOCIDO (ni baremación ni puntuaciones)")
    return [], [], "desconocido"


def marcar_ultima_version(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    # idxmax() por grupo solo da UNA fila (índice), no todas las filas del PDF que
    # tiene la marca de tiempo más reciente para ese (especialidad, tribunal, tipo) —
    # con ~30-50 opositores por PDF eso dejaba fuera casi todas las filas de la
    # versión "última". transform("max") + comparación sí marca todas las filas de
    # ese PDF.
    marca_maxima_grupo = df.groupby(
        ["Especialidad", "Tribunal", "Tipo Publicación"]
    )["Marca Tiempo"].transform("max")

    df["Es_Ultima_Version"] = df["Marca Tiempo"] == marca_maxima_grupo

    return df


def main():
    convocatoria_dir = os.path.join(str(BASE_DIR), f"{ANYO}-{CONVOCATORIA}")

    if not os.path.isdir(convocatoria_dir):
        print(f"No existe la carpeta de descargas: {convocatoria_dir}")
        sys.exit(1)

    registros_puntuaciones = []
    registros_baremacion = []
    ficheros_sin_reconocer = []

    total_pdfs = 0
    total_error = 0
    total_desconocido = 0

    for especialidad in sorted(ESPECIALIDADES):
        carpeta_pdf = os.path.join(
            convocatoria_dir, f"{CUERPO}-{especialidad}", "pdf"
        )

        pdfs = sorted(glob.glob(os.path.join(carpeta_pdf, "*.pdf")))

        if not pdfs:
            continue

        print()
        print("=" * 80)
        print(f"{especialidad} ({ESPECIALIDADES[especialidad]}) — {len(pdfs)} PDFs")
        print("=" * 80)

        for ruta_pdf in pdfs:
            total_pdfs += 1
            nombre_fichero = os.path.basename(ruta_pdf)

            m = NOMBRE_RE.match(os.path.splitext(nombre_fichero)[0])

            if not m:
                print(f"  NOMBRE NO RECONOCIDO: {nombre_fichero}")
                ficheros_sin_reconocer.append(nombre_fichero)
                continue

            metadatos = {
                "Especialidad": m.group("especialidad"),
                "Tribunal": int(m.group("tribunal")),
                "Tipo Publicación": m.group("tipo"),
                "Marca Tiempo": m.group("marca_tiempo"),
                "Fichero": nombre_fichero,
            }

            print(f"  {nombre_fichero}", end=" -> ")

            filas_punt, filas_bar, resultado = procesar_pdf(ruta_pdf, metadatos)

            registros_puntuaciones.extend(filas_punt)
            registros_baremacion.extend(filas_bar)

            if resultado == "error_lectura":
                total_error += 1
            elif resultado == "desconocido":
                total_desconocido += 1
            else:
                print(f"{resultado}, {len(filas_punt) + len(filas_bar)} filas")

    # ========================================================
    # DATAFRAMES + EXCEL
    # ========================================================

    df_puntuaciones = pd.DataFrame(registros_puntuaciones)
    df_baremacion = pd.DataFrame(registros_baremacion)

    df_puntuaciones = marcar_ultima_version(df_puntuaciones)
    df_baremacion = marcar_ultima_version(df_baremacion)

    carpeta_xlsx = os.path.join(convocatoria_dir, "xlsx")
    os.makedirs(carpeta_xlsx, exist_ok=True)

    ruta_excel = os.path.join(
        carpeta_xlsx, f"{ANYO}-{CONVOCATORIA}_resultados.xlsx"
    )

    with pd.ExcelWriter(ruta_excel, engine="openpyxl") as writer:
        if not df_puntuaciones.empty:
            df_puntuaciones.to_excel(writer, sheet_name="Puntuaciones", index=False)
            df_puntuaciones[df_puntuaciones["Es_Ultima_Version"]].to_excel(
                writer, sheet_name="Puntuaciones (última versión)", index=False
            )

        if not df_baremacion.empty:
            df_baremacion.to_excel(writer, sheet_name="Baremacion", index=False)
            df_baremacion[df_baremacion["Es_Ultima_Version"]].to_excel(
                writer, sheet_name="Baremacion (última versión)", index=False
            )

        if ficheros_sin_reconocer:
            pd.DataFrame({"Fichero": ficheros_sin_reconocer}).to_excel(
                writer, sheet_name="Nombres no reconocidos", index=False
            )

        for hoja, worksheet in writer.sheets.items():
            worksheet.auto_filter.ref = worksheet.dimensions
            worksheet.freeze_panes = "A2"

    print()
    print("=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print("PDFs procesados:", total_pdfs)
    print("Filas de puntuaciones:", len(df_puntuaciones))
    print("Filas de baremación:", len(df_baremacion))
    print("PDFs con formato no reconocido:", total_desconocido)
    print("PDFs con error de lectura:", total_error)
    print("Nombres de fichero no reconocidos:", len(ficheros_sin_reconocer))
    print("Excel generado en:", ruta_excel)


if __name__ == "__main__":
    main()
