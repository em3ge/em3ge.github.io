"""Guarda y sube solo lo que haya cambiado en los proyectos de este ordenador.

    python guardar.py

De cada proyecto de local.json: si hay cambios, los guarda en git con la fecha y los
sube a GitHub. Si algun proyecto ha cambiado, rehace la web (fechas y tamano) y la sube.
No pregunta nada ni abre ventanas: esta pensado para una tarea programada.
Lo que hace queda apuntado en guardar.log."""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
REGISTRO = RAIZ / "guardar.log"
SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
ENTORNO = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
lineas = []


def decir(texto):
    lineas.append(f"{datetime.now():%Y-%m-%d %H:%M} {texto}")
    try:
        print(texto, flush=True)
    except (OSError, AttributeError, ValueError):
        pass


def git(carpeta, *args):
    try:
        r = subprocess.run(["git", "-C", str(carpeta), *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300, env=ENTORNO,
                           creationflags=SIN_VENTANA)
        return r.returncode, (r.stdout + r.stderr).strip()
    except (OSError, subprocess.SubprocessError) as error:
        return 1, str(error)


def guardar(nombre, carpeta, mensaje):
    """Devuelve True si se ha guardado algo nuevo."""
    carpeta = Path(carpeta)
    if not (carpeta / ".git").exists():
        decir(f"NO  {nombre}: no es un repositorio de git")
        return False
    git(carpeta, "add", "-A")
    nuevo = git(carpeta, "diff", "--cached", "--quiet")[0] != 0
    if nuevo:
        cod, salida = git(carpeta, "commit", "-m", mensaje)
        if cod != 0:
            decir(f"NO  {nombre}: no se pudo guardar: {salida.splitlines()[-1] if salida else ''}")
            return False
    # Subir tambien lo que quedara sin subir de otra vez
    if git(carpeta, "remote")[1]:
        pendiente = git(carpeta, "rev-list", "--count", "@{u}..HEAD")
        if nuevo or pendiente[0] != 0 or pendiente[1] not in ("0", ""):
            cod, salida = git(carpeta, "push")
            if cod != 0:
                decir(f"NO  {nombre}: guardado aqui, pero no se pudo subir: "
                      f"{salida.splitlines()[-1] if salida else ''}")
                return nuevo
            decir(f"BIEN  {nombre}: guardado y subido")
    elif nuevo:
        decir(f"BIEN  {nombre}: guardado (sin sitio al que subir)")
    return nuevo


def main():
    try:
        aqui = json.loads((RAIZ / "local.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        aqui = {}
    mensaje = f"Guardado automatico del {datetime.now():%Y-%m-%d %H:%M}"
    cambiados = [n for n, c in aqui.items() if not n.startswith("_") and guardar(n, c, mensaje)]
    if cambiados:
        sys.path.insert(0, str(RAIZ))
        try:
            import generar
            generar.generar()
        except Exception as error:  # la web no debe impedir que se guarde el codigo
            decir(f"NO  la web no se pudo rehacer: {error}")
    guardar("proyectos-web", RAIZ, "Actualiza la web de proyectos")
    if not lineas:
        lineas.append(f"{datetime.now():%Y-%m-%d %H:%M} sin cambios")
    try:
        antes = REGISTRO.read_text(encoding="utf-8").splitlines() if REGISTRO.is_file() else []
        REGISTRO.write_text("\n".join((antes + lineas)[-300:]) + "\n", encoding="utf-8")
    except OSError:
        pass


if __name__ == "__main__":
    main()
