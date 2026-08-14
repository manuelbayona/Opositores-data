from pathlib import Path
from config import *

import re
import pdfplumber

# ============================================================
# CARPETAS
# ============================================================

CARPETA = Path(RUTA_DATOS)

CARPETA_HTML = CARPETA / "html"
CARPETA_PDF = CARPETA / "pdf"
CARPETA_TXT = CARPETA / "txt"
CARPETA_XLSX = CARPETA / "xlsx"

CARPETA.mkdir(parents=True, exist_ok=True)

CARPETA_HTML.mkdir(exist_ok=True)
CARPETA_PDF.mkdir(exist_ok=True)
CARPETA_TXT.mkdir(exist_ok=True)
CARPETA_XLSX.mkdir(exist_ok=True)

# ============================================================
# CONTADORES
# ============================================================

pdfs_procesados = 0
pdfs_con_texto = 0

# ============================================================
# RECORRER PDFS
# ============================================================

for fichero in sorted(CARPETA_PDF.glob("*.pdf")):

    pdfs_procesados += 1

    print("=" * 80)
    print(f"PROCESANDO: {fichero.name}")

    texto = ""

    try:

        with pdfplumber.open(str(fichero)) as pdf:

            print(f"Páginas: {len(pdf.pages)}")

            for pagina in pdf.pages:

                txt = pagina.extract_text()

                if txt:
                    texto += "\n" + txt

        if not texto.strip():

            print("PDF SIN TEXTO")
            continue

        pdfs_con_texto += 1

    except Exception as e:

        print(f"ERROR leyendo {fichero.name}: {e}")
        continue

    print(
        f"Caracteres extraídos: {len(texto)}"
    )

    # ========================================================
    # GUARDAR TXT EN /txt
    # ========================================================

    txt_destino = (
        CARPETA_TXT /
        f"{fichero.stem}.txt"
    )

    with open(
        txt_destino,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(texto)

    print(
        f"Texto guardado en: {txt_destino}"
    )

    # ========================================================
    # MUESTRA
    # ========================================================

    print("\nINICIO DEL TEXTO EXTRAÍDO:")
    print(texto[:1000])
    print("\nFIN MUESTRA\n")

# ============================================================
# RESUMEN
# ============================================================

print()
print("=" * 80)
print(
    f"PDFs procesados: {pdfs_procesados}"
)
print(
    f"PDFs con texto: {pdfs_con_texto}"
)
print("=" * 80)

print()
print("TXT generados en:")
print(CARPETA_TXT)

print()
print("La generación del Excel queda delegada a:")
print("txt_a_excel.py")