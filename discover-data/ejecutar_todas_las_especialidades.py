import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CUERPO = "0597"

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

BASE_DATOS = Path(
    r"C:\Users\JI53BQ\OneDrive - ING\Desktop\tribunales\src"
)

SCRIPTS = [
    "tribunales.py",
    "extraer_notas.py",
    "unir_txts.py",
    "txt_a_excel.py"
]

for especialidad in ESPECIALIDADES:

    print()
    print("=" * 80)
    print(
        f"EJECUTANDO ESPECIALIDAD {especialidad}"
    )
    print("=" * 80)

    ruta_datos = (
        BASE_DATOS /
        f"{CUERPO}-{especialidad}"
    )

    env = os.environ.copy()

    env["ESPECIALIDAD"] = especialidad
    env["RUTA_DATOS"] = str(ruta_datos)

    print("RUTA_DATOS =", ruta_datos)

    for script in SCRIPTS:

        print()
        print("=" * 80)
        print(f"EJECUTANDO: {script}")
        print("=" * 80)

        resultado = subprocess.run(
            [sys.executable, str(BASE_DIR / script)],
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
print("TODAS LAS ESPECIALIDADES PROCESADAS")
print("=" * 80)