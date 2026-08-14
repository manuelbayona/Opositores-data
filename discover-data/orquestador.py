import os
import sys
import subprocess

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

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

SCRIPTS = [
    "tribunales.py",
    "extraer_notas.py",
    "unir_txts.py",
    "txt_a_excel.py",
    "recopilar_excels.py"
]

for especialidad in ESPECIALIDADES:

    print()
    print("=" * 80)
    print(
        f"EJECUTANDO ESPECIALIDAD {especialidad}"
    )
    print("=" * 80)

    env = os.environ.copy()

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
                f"ERROR EN {script}"
            )

            sys.exit(
                resultado.returncode
            )

print()
print("=" * 80)
print("TODAS LAS ESPECIALIDADES FINALIZADAS")
print("=" * 80)