"""
Descarga los listados de interés (calificaciones/puntuaciones/baremación) para todas
las especialidades de una o varias convocatorias, llamando a descargar_listados.py
una vez por cada combinación convocatoria x especialidad.

Para una sola especialidad/convocatoria basta con ejecutar descargar_listados.py
directamente (ver README.md). Este script es para recorrerlas todas de una vez.
"""

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# Una entrada por convocatoria a procesar. Añade más aquí para descargar varias
# convocatorias en una sola ejecución (ANYO/CONVOCATORIA se pasan a config.py por
# variable de entorno, ver ese fichero).
CONVOCATORIAS = [
    {"anyo": "2026", "convocatoria": "OPOPRI26"},
       {"anyo": "2024", "convocatoria": "OPOPRI24"},
        {"anyo": "2022", "convocatoria": "OPOPRI22"}
]

ESPECIALIDADES = [
    "AL",
    "EF",
    "EI",
    "FF",
    "FI",
    "MU",
    "PRI",
    "PT",
]

for convocatoria in CONVOCATORIAS:

    print()
    print("#" * 80)
    print(
        f"CONVOCATORIA {convocatoria['convocatoria']} ({convocatoria['anyo']})"
    )
    print("#" * 80)

    for especialidad in ESPECIALIDADES:

        print()
        print("=" * 80)
        print(
            f"EJECUTANDO ESPECIALIDAD {especialidad}"
        )
        print("=" * 80)

        env = os.environ.copy()

        env["ANYO"] = convocatoria["anyo"]
        env["CONVOCATORIA"] = convocatoria["convocatoria"]
        env["ESPECIALIDAD"] = especialidad

        resultado = subprocess.run(
            [sys.executable, "descargar_listados.py"],
            cwd=BASE_DIR,
            env=env
        )

        if resultado.returncode != 0:

            print()
            print(
                f"ERROR EN descargar_listados.py "
                f"(convocatoria {convocatoria['convocatoria']}, "
                f"especialidad {especialidad})"
            )

            sys.exit(
                resultado.returncode
            )

print()
print("=" * 80)
print("TODAS LAS CONVOCATORIAS Y ESPECIALIDADES FINALIZADAS")
print("=" * 80)
