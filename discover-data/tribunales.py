import re
import requests

from io import BytesIO
from pathlib import Path
from pypdf import PdfReader

from config import *

from pathlib import Path
from config import *

print("=" * 80)
print("CONFIG ACTIVA")
print("=" * 80)
print("CUERPO      =", CUERPO)
print("ESPECIALIDAD=", ESPECIALIDAD)
print("RUTA_DATOS  =", RUTA_DATOS)
print("=" * 80)

BASE_URL = (
    "https://servicios.educarm.es/admin/index2.php"
    "?aplicacion=PUBLICACIONES_TRIBUNALES"
    "&module=publicacionesTribunales"
    "&action=getPublicaciones"
    "&anyo=2026"
    "&convocatoria=OPOPRI26"
)

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
    "Content-Type": "application/x-www-form-urlencoded"
}

COOKIE = ""

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
# PROCESO
# =====================================================

no_descargados = []

session = requests.Session()

for numero in range(
    TRIBUNAL_DESDE,
    TRIBUNAL_HASTA + 1
):

    tribunal = f"{numero:02d}"

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