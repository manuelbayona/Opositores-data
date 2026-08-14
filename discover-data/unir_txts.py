from pathlib import Path
from config import *

# ============================================================
# CONFIG
# ============================================================

CARPETA = Path(RUTA_DATOS)

SALIDA = CARPETA / "TODOS_LOS_TXT_UNIDOS.txt"

CARPETA_TXT = CARPETA / "txt"

print("=" * 80)
print("UNIR_TXTS")
print("=" * 80)
print("CARPETA =", CARPETA)
print("TXT =", CARPETA_TXT)
print("SALIDA =", SALIDA)
print("=" * 80)

txts = sorted(
    CARPETA_TXT.glob("*.txt")
)



# ============================================================
# UNIR
# ============================================================

with open(
    SALIDA,
    "w",
    encoding="utf-8",
    errors="ignore"
) as fout:

    for fichero in txts:

        print(f"Procesando: {fichero}")

        fout.write("\n")
        fout.write("=" * 120 + "\n")
        fout.write(f"FICHERO: {fichero.name}\n")
        fout.write("=" * 120 + "\n\n")

        try:

            with open(
                fichero,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as fin:

                fout.write(fin.read())

        except Exception as e:

            fout.write(
                f"\nERROR LEYENDO FICHERO: {e}\n"
            )

        fout.write("\n\n")

print()
print(f"Fichero generado: {SALIDA}")
print(f"Total txt procesados: {len(txts)}")