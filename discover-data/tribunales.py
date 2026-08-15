import os
import re
import requests

from io import BytesIO
from pathlib import Path
from pypdf import PdfReader

from config import *

print("=" * 80)
print("CONFIG ACTIVA")
print("=" * 80)
print("ANYO        =", ANYO)
print("CONVOCATORIA=", CONVOCATORIA)
print("CUERPO      =", CUERPO)
print("ESPECIALIDAD=", ESPECIALIDAD)
print("RUTA_DATOS  =", RUTA_DATOS)
print("=" * 80)

# ANYO/CONVOCATORIA now come from config.py (env-var overridable) instead of being
# hardcoded here, so the same script works for any convocatoria without editing it.
INDEX_URL = "https://servicios.educarm.es/admin/index2.php"

BASE_QS = (
    "?aplicacion=PUBLICACIONES_TRIBUNALES"
    "&module=publicacionesTribunales"
    f"&anyo={ANYO}"
    f"&convocatoria={CONVOCATORIA}"
)

# Same base URL as before, just built from INDEX_URL/BASE_QS so it stays in sync with
# the discovery endpoints below instead of being duplicated.
BASE_URL = f"{INDEX_URL}{BASE_QS}&action=getPublicaciones"

# Portal page a browser would have been on before submitting the form — sent as
# Referer, per the real captured request (see 2026-murcia-maestros/requests/*.har).
REFERER = f"{INDEX_URL}{BASE_QS}"

# =====================================================
# CARPETAS
# =====================================================

CARPETA = Path(RUTA_DATOS)

CARPETA_HTML = CARPETA / "html"
CARPETA_PDF = CARPETA / "pdf"

CARPETA.mkdir(parents=True, exist_ok=True)
CARPETA_HTML.mkdir(exist_ok=True)
CARPETA_PDF.mkdir(exist_ok=True)

# =====================================================
# HEADERS
# =====================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://servicios.educarm.es",
    "Referer": REFERER,
}

# A captured real browser request to this same endpoint (2026-murcia-maestros/requests/*.har)
# carried no Cookie header at all and was accepted (response header `rdwr_response: allowed`)
# — this form does not require a session. Kept here, off by default, only in case a future
# convocatoria's portal configuration does gate on one; a session cookie is a credential and
# must never be committed to the repo (paste it in your shell for this run only, e.g.
# EDUCARM_COOKIE='...' python3 tribunales.py).
COOKIE = os.getenv("EDUCARM_COOKIE", "")

if COOKIE:
    HEADERS["Cookie"] = COOKIE

# =====================================================
# VALIDAR PDF
# =====================================================

def pdf_es_valido(pdf_bytes):

    try:

        reader = PdfReader(
            BytesIO(pdf_bytes)
        )

        lineas = []

        for page in reader.pages:

            try:

                texto = (
                    page.extract_text()
                    or ""
                )

            except Exception:
                continue

            for linea in texto.splitlines():

                linea = " ".join(
                    linea.upper().split()
                )

                if linea:
                    lineas.append(linea)

        texto_buscado = " ".join(
            PDF_TEXTO_EXACTO.upper().split()
        )

        for linea in lineas:

            if linea == texto_buscado:

                print(
                    f"  VALIDO -> [{texto_buscado}]"
                )

                return True

        return False

    except Exception as e:

        print(
            f"  ERROR VALIDANDO PDF: {e}"
        )

        return False


# =====================================================
# DESCUBRIR TRIBUNALES REALES (en vez de fuerza bruta 1-50)
# =====================================================
# El formulario real del portal encadena dos llamadas AJAX antes de pedir las
# publicaciones (ver 2026-murcia-maestros/requests/*.har, entradas 1 y 2):
#   ajaxOpcionesEspecialidad(codCuerpo, anyo, convocatoria)
#   ajaxOpcionesTribunal(codCuerpo, codEspecialidad, anyo, convocatoria)
# Ambas devuelven un fragmento HTML con <option value="...">...</option> — se asume
# ese formato (típico de estos paneles PHP) porque el HAR capturado no incluyó el
# cuerpo de la respuesta, solo cabeceras/tamaño. Si el parseo no encuentra nada, se
# guarda la respuesta cruda para poder ajustarlo, y se cae al rango fijo
# TRIBUNAL_DESDE..TRIBUNAL_HASTA como hacía el script original.

OPTION_RE = re.compile(
    r'<option[^>]*\bvalue="([^"]+)"[^>]*>',
    re.I,
)


def descubrir_tribunales(especialidad):

    data = {
        "codCuerpo": CUERPO,
        "codEspecialidad": especialidad,
        "anyo": ANYO,
        "convocatoria": CONVOCATORIA,
    }

    try:
        r = session.post(
            f"{INDEX_URL}{BASE_QS}&action=ajaxOpcionesTribunal",
            data=data,
            headers=HEADERS,
            timeout=60,
        )
    except Exception as e:
        print(f"  ERROR CONSULTANDO TRIBUNALES: {e}")
        return []

    valores = [v for v in OPTION_RE.findall(r.text) if v.strip()]

    if not valores:
        debug_file = CARPETA_HTML / f"debug_ajaxOpcionesTribunal_{especialidad}.html"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(r.text)
        print(f"  NO SE ENCONTRARON TRIBUNALES (respuesta guardada en {debug_file})")

    return valores


# =====================================================
# PROCESO
# =====================================================

no_descargados = []

session = requests.Session()

tribunales_descubiertos = descubrir_tribunales(ESPECIALIDAD)

if tribunales_descubiertos:
    print(f"TRIBUNALES DESCUBIERTOS PARA {ESPECIALIDAD}: {tribunales_descubiertos}")
    numeros_tribunal = tribunales_descubiertos
else:
    print("SIN DESCUBRIMIENTO -> USANDO RANGO FIJO TRIBUNAL_DESDE..TRIBUNAL_HASTA")
    numeros_tribunal = [f"{n:02d}" for n in range(TRIBUNAL_DESDE, TRIBUNAL_HASTA + 1)]

for tribunal in numeros_tribunal:

    print()
    print("=" * 80)
    print(f"TRIBUNAL {tribunal}")
    print("=" * 80)

    pdf_destino = (
        CARPETA_PDF /
        f"{ESPECIALIDAD}-{tribunal}.pdf"
    )

    if pdf_destino.exists():

        print("PDF YA EXISTE")
        continue

    data = {
        "cuerpos_lista": CUERPO,
        "especialidades_lista": ESPECIALIDAD,
        "tribunales_lista": tribunal,
    }

    try:

        r = session.post(
            BASE_URL,
            data=data,
            headers=HEADERS,
            timeout=60
        )

        html = r.text

        html_file = (
            CARPETA_HTML /
            f"Tribunal_{tribunal}.html"
        )

        with open(
            html_file,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(html)

        if NOMBRE_DOCUMENTO not in html:

            print(
                "NO APARECE EL DOCUMENTO"
            )

            no_descargados.append(
                tribunal
            )

            continue

        filas = re.findall(
            r"<tr.*?</tr>",
            html,
            re.I | re.S
        )

        fila_objetivo = None

        for fila in filas:

            if NOMBRE_DOCUMENTO in fila:

                fila_objetivo = fila
                break

        if fila_objetivo is None:
            fila_objetivo = html

        pdfs = re.findall(
            r'https?://[^"\']+\.pdf|/[^"\']+\.pdf',
            fila_objetivo,
            re.I
        )

        if not pdfs:

            pdfs = re.findall(
                r'https?://[^"\']+\.pdf|/[^"\']+\.pdf',
                html,
                re.I
            )

        if not pdfs:

            print("NO ENCUENTRO PDF")

            no_descargados.append(
                tribunal
            )

            continue

        pdf_valido = False

        for pdf_url in pdfs:

            try:

                if pdf_url.startswith("/"):

                    pdf_url = (
                        "https://servicios.educarm.es"
                        + pdf_url
                    )

                print(
                    f"PROBANDO PDF: {pdf_url}"
                )

                pdf = session.get(
                    pdf_url,
                    headers=HEADERS,
                    timeout=60
                )

                if pdf.status_code != 200:
                    continue

                if not pdf_es_valido(
                    pdf.content
                ):

                    print(
                        "DESCARTADO"
                    )

                    continue

                with open(
                    pdf_destino,
                    "wb"
                ) as f:

                    f.write(
                        pdf.content
                    )

                print(
                    "PDF CORRECTO DESCARGADO"
                )

                pdf_valido = True

                break

            except Exception as e:

                print(
                    f"ERROR PDF: {e}"
                )

        if not pdf_valido:

            print(
                "NINGUN PDF CUMPLE EL FILTRO"
            )

            no_descargados.append(
                tribunal
            )

    except Exception as e:

        print(
            f"ERROR: {e}"
        )

        no_descargados.append(
            tribunal
        )

# =====================================================
# RESUMEN
# =====================================================

print()
print("=" * 80)
print("TRIBUNALES SIN DESCARGA")
print("=" * 80)

for t in sorted(
    set(no_descargados)
):
    print(t)

with open(
    CARPETA /
    "tribunales_no_descargados.txt",
    "w",
    encoding="utf-8"
) as f:

    for t in sorted(
        set(no_descargados)
    ):
        f.write(f"{t}\n")