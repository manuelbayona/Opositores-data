#!/usr/bin/env python3

import os
import shutil
from pathlib import Path

# Carpeta raíz desde donde empezar la búsqueda
ROOT_DIR = Path(".").resolve()

# Carpeta destino
DEST_DIR = ROOT_DIR / "EXCELS_RECOPILADOS"
DEST_DIR.mkdir(exist_ok=True)

# Extensiones Excel
EXCEL_EXTENSIONS = {".xlsx", ".xls", ".xlsm", ".xlsb"}

copiados = 0

for file in ROOT_DIR.rglob("*"):
    if (
            file.is_file()
            and file.suffix.lower() in EXCEL_EXTENSIONS
            and DEST_DIR not in file.parents
    ):
        destino = DEST_DIR / file.name

        # Evitar sobrescribir si ya existe
        if destino.exists():
            base = destino.stem
            ext = destino.suffix
            contador = 1

            while True:
                nuevo_destino = DEST_DIR / f"{base}_{contador}{ext}"
                if not nuevo_destino.exists():
                    destino = nuevo_destino
                    break
                contador += 1

        shutil.copy2(file, destino)
        copiados += 1
        print(f"Copiado: {file} -> {destino}")

print(f"\nProceso finalizado. Total de Excel copiados: {copiados}")
print(f"Carpeta destino: {DEST_DIR}")