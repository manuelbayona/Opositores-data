import os
import sys
import subprocess

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# One entry per convocatoria to process. Add more entries here instead of editing
# tribunales.py's BASE_URL by hand for every new convocatoria (ANYO/CONVOCATORIA now
# live in config.py, env-var overridable — see that file).
CONVOCATORIAS = [
    {"anyo": "2026", "convocatoria": "OPOPRI26"},
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

# descargar_listados.py sustituye a tribunales.py: descarga solo los PDFs de interés
# (calificaciones/puntuaciones/baremación) filtrando por su título real en el portal,
# en vez de traerse todo lo publicado por tribunal y abrir cada PDF para comprobarlo.
SCRIPTS = [
    "descargar_listados.py",
    "extraer_notas.py",
    "unir_txts.py",
    "txt_a_excel.py",
    "recopilar_excels.py"
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

        for script in SCRIPTS:

            print()
            print("=" * 80)
            print(
                f"EJECUTANDO: {script}"
            )
            print("=" * 80)

            resultado = subprocess.run(
                [sys.executable, script],
                cwd=BASE_DIR,
                env=env
            )

            if resultado.returncode != 0:

                print()
                print(
                    f"ERROR EN {script} "
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
