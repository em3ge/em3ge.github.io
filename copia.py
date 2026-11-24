"""Copia de seguridad de los proyectos de este ordenador.

    python copia.py

De cada proyecto de local.json, y de esta misma web, guarda un archivo con todo
su historial de git (un "bundle") en la carpeta de copias. Se conservan las ocho
ultimas copias de cada uno.

La carpeta de copias es OneDrive\\Copias-proyectos, o la que diga "_copias" en local.json.

Para recuperar un proyecto desde una copia:
    git clone NOMBRE_DE_LA_COPIA.bundle carpeta-nueva"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
GUARDAR = 8


def main():
    try:
        aqui = json.loads((RAIZ / "local.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        aqui = {}
    destino = aqui.pop("_copias", "") or os.path.join(
        os.environ.get("OneDrive") or str(Path.home() / "OneDrive"), "Copias-proyectos")
    destino = Path(destino)
    proyectos = dict(aqui)
    proyectos["proyectos-web"] = str(RAIZ)
    marca = datetime.now().strftime("%Y-%m-%d_%H%M")
    fallos = 0
    for nombre, carpeta in proyectos.items():
        carpeta = Path(carpeta)
        if not (carpeta / ".git").exists():
            print(f"NO  {nombre}: no es un repositorio de git ({carpeta})")
            fallos += 1
            continue
        sitio = destino / nombre
        sitio.mkdir(parents=True, exist_ok=True)
        archivo = sitio / f"{nombre}_{marca}.bundle"
        r = subprocess.run(["git", "-C", str(carpeta), "bundle", "create", str(archivo), "--all"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0 or not archivo.is_file():
            print(f"NO  {nombre}: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'fallo'}")
            fallos += 1
            continue
        sucio = subprocess.run(["git", "-C", str(carpeta), "status", "--porcelain"],
                               capture_output=True, text=True).stdout.strip()
        aviso = "  (OJO: hay cambios sin guardar en git que no van en la copia)" if sucio else ""
        print(f"BIEN  {nombre}: {archivo.name}, {archivo.stat().st_size / 1e6:.1f} MB{aviso}")
        for viejo in sorted(sitio.glob("*.bundle"))[:-GUARDAR]:
            viejo.unlink()
    print(f"Copias en {destino}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
