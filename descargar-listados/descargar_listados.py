"""
Descarga solo los listados de resultados (calificaciones/puntuaciones/baremación)
publicados por tribunal, para una convocatoria/especialidad — no todo lo publicado.

Sustituye a tribunales.py para este caso de uso: aquel descargaba TODOS los PDFs de
cada tribunal y luego abría cada uno para comprobar si era el buscado. Ahora que
conocemos la estructura real de la página de publicaciones (ver
2026-murcia-maestros/requests/response4.har), cada documento trae ya un título legible
en el propio listado ("Calificaciones segunda prueba", "Puntuaciones obtenidas fase
oposición", "Listado baremación - Acceso 1"...) frente al ruido puramente
administrativo ("CITACIÓN A DETERMINADOS ASPIRANTES", "PLAZO DE PRESENTACIÓN DE
RECLAMACIONES...") — así que se puede decidir qué interesa sin descargar nada primero.

Variables de convocatoria/especialidad/palabras de interés: ver config.py, todas
sobreescribibles por variable de entorno.
"""

import os
import re
import unicodedata

import requests

from pathlib import Path

from config import *

print("=" * 80)
print("CONFIG ACTIVA")
print("=" * 80)
print("ANYO        =", ANYO)
print("CONVOCATORIA=", CONVOCATORIA)
print("CUERPO      =", CUERPO)
print("ESPECIALIDAD=", ESPECIALIDAD)
print("RUTA_DATOS  =", RUTA_DATOS)
print("PALABRAS_CLAVE_INTERES =", PALABRAS_CLAVE_INTERES)
print("=" * 80)

# =====================================================
# URLS
# =====================================================

INDEX_URL = "https://servicios.educarm.es/admin/index2.php"

BASE_QS = (
    "?aplicacion=PUBLICACIONES_TRIBUNALES"
    "&module=publicacionesTribunales"
    f"&anyo={ANYO}"
    f"&convocatoria={CONVOCATORIA}"
)

BASE_URL = f"{INDEX_URL}{BASE_QS}&action=getPublicaciones"
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

# Igual que en tribunales.py: la petición real capturada no llevaba ninguna cookie y
# fue aceptada por el portal — este formulario no exige sesión. Se deja como
# posibilidad por variable de entorno, nunca como valor fijo en el fichero.
COOKIE = os.getenv("EDUCARM_COOKIE", "")

if COOKIE:
    HEADERS["Cookie"] = COOKIE

session = requests.Session()

# =====================================================
# FILTRO DE INTERÉS
# =====================================================


def normalizar(texto):
    """Mayúsculas y sin tildes, para comparar sin depender de acentos."""

    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

    return sin_tildes.upper()


PALABRAS_CLAVE_NORMALIZADAS = [
    normalizar(palabra.strip())
    for palabra in PALABRAS_CLAVE_INTERES
    if palabra.strip()
]

PALABRAS_EXCLUIR_NORMALIZADAS = [
    normalizar(palabra.strip())
    for palabra in PALABRAS_CLAVE_EXCLUIR
    if palabra.strip()
]


def es_de_interes(nombre_fichero, titulo_legible):

    texto = normalizar(f"{nombre_fichero} {titulo_legible}")

    if any(clave in texto for clave in PALABRAS_EXCLUIR_NORMALIZADAS):
        return False

    return any(
        clave in texto
        for clave in PALABRAS_CLAVE_NORMALIZADAS
    )


# Cada publicación aparece como DOS enlaces al mismo PDF: uno con el nombre de
# fichero (class="colorRojo1") y otro con el título legible del documento
# (class="colorRojo2") — ver 2026-murcia-maestros/requests/response4.har. Con el
# segundo basta para decidir si interesa.
ENLACE_RE = re.compile(
    r'<a\s+href="([^"]+\.pdf)"\s+class="colorRojo2"[^>]*>([^<]+)</a>',
    re.I,
)

OPTION_RE = re.compile(
    r'<option[^>]*\bvalue="([^"]+)"[^>]*>',
    re.I,
)

# =====================================================
# DESCUBRIR TRIBUNALES REALES (en vez de fuerza bruta 1-50)
# =====================================================


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
# DESCARGA POR TRIBUNAL
# =====================================================


def descargar_publicaciones_tribunal(especialidad, tribunal):

    data = {
        "cuerpos_lista": CUERPO,
        "especialidades_lista": especialidad,
        "tribunales_lista": tribunal,
    }

    try:
        r = session.post(BASE_URL, data=data, headers=HEADERS, timeout=60)
    except Exception as e:
        print(f"  ERROR: {e}")
        return

    html_file = CARPETA_HTML / f"Tribunal_{tribunal}.html"

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(r.text)

    publicaciones = ENLACE_RE.findall(r.text)

    if not publicaciones:
        print("  SIN PUBLICACIONES O FORMATO NO RECONOCIDO "
              f"(respuesta guardada en {html_file})")
        return

    interesantes = [
        (url, titulo.strip())
        for url, titulo in publicaciones
        if es_de_interes(url, titulo)
    ]

    descartadas = len(publicaciones) - len(interesantes)

    print(
        f"  {len(publicaciones)} publicaciones encontradas, "
        f"{len(interesantes)} de interés, {descartadas} descartadas"
    )

    for url, titulo in interesantes:

        nombre_fichero = url.rsplit("/", 1)[-1]
        pdf_destino = CARPETA_PDF / nombre_fichero

        if pdf_destino.exists():
            print(f"    YA EXISTE: {titulo} -> {nombre_fichero}")
            continue

        try:
            pdf = session.get(url, headers=HEADERS, timeout=60)

            if pdf.status_code != 200:
                print(f"    ERROR HTTP {pdf.status_code}: {titulo}")
                continue

            with open(pdf_destino, "wb") as f:
                f.write(pdf.content)

            print(f"    DESCARGADO: {titulo} -> {nombre_fichero}")

        except Exception as e:
            print(f"    ERROR DESCARGANDO {titulo}: {e}")


# =====================================================
# PROCESO
# =====================================================
# Detrás de un "if __name__" a propósito: importar este módulo (por ejemplo para
# reutilizar es_de_interes/ENLACE_RE en una prueba sin red) NUNCA debe disparar
# peticiones HTTP reales por sí solo.


def main():

    tribunales = descubrir_tribunales(ESPECIALIDAD)

    if tribunales:
        print(f"TRIBUNALES DESCUBIERTOS PARA {ESPECIALIDAD}: {tribunales}")
    else:
        print("SIN DESCUBRIMIENTO -> USANDO RANGO FIJO TRIBUNAL_DESDE..TRIBUNAL_HASTA")
        tribunales = [f"{n:02d}" for n in range(TRIBUNAL_DESDE, TRIBUNAL_HASTA + 1)]

    for tribunal in tribunales:

        print()
        print("=" * 80)
        print(f"TRIBUNAL {tribunal}")
        print("=" * 80)

        descargar_publicaciones_tribunal(ESPECIALIDAD, tribunal)


if __name__ == "__main__":
    main()
