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
choques = []


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
    if not git(carpeta, "remote")[1]:
        if nuevo:
            decir(f"BIEN  {nombre}: guardado (sin sitio al que subir)")
        return nuevo
    # Traer lo que otro ordenador haya subido, y poner lo de aqui encima
    cod, salida = git(carpeta, "fetch")
    if cod != 0:
        decir(f"NO  {nombre}: sin conexion con GitHub: {salida.splitlines()[-1] if salida else ''}")
        return nuevo
    detras = git(carpeta, "rev-list", "--count", "HEAD..@{u}")[1]
    if detras not in ("0", ""):
        cod, salida = git(carpeta, "rebase", "@{u}")
        if cod != 0:
            git(carpeta, "rebase", "--abort")
            decir(f"NO  {nombre}: HAY DOS VERSIONES. El mismo archivo se ha cambiado en dos ordenadores.")
            choques.append(nombre)
            return nuevo
        decir(f"BIEN  {nombre}: traido lo nuevo de GitHub")
    delante = git(carpeta, "rev-list", "--count", "@{u}..HEAD")
    if delante[0] != 0 or delante[1] not in ("0", ""):
        cod, salida = git(carpeta, "push")
        if cod != 0:
            decir(f"NO  {nombre}: guardado aqui, pero no se pudo subir: "
                  f"{salida.splitlines()[-1] if salida else ''}")
            return nuevo
        decir(f"BIEN  {nombre}: guardado y subido")
    return nuevo


def avisar():
    """Ventana de aviso si quedaron dos versiones. Como mucho una cada seis horas."""
    marca = RAIZ / "guardar.aviso"
    try:
        if marca.is_file() and datetime.now().timestamp() - marca.stat().st_mtime < 6 * 3600:
            return
        marca.write_text(", ".join(choques), encoding="utf-8")
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0, "Hay dos versiones distintas de: " + ", ".join(choques) + ".\n\n"
            "El mismo archivo se cambió en dos ordenadores antes de sincronizar. No se ha perdido nada: "
            "lo de este ordenador está guardado aquí y lo del otro está en GitHub.\n\n"
            "Abre Claude en la carpeta del proyecto y dile: «hay dos versiones, júntalas».",
            "Proyectos sin sincronizar", 0x30 | 0x40000)
    except (OSError, AttributeError):
        pass


def main():
    try:
        aqui = json.loads((RAIZ / "local.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        aqui = {}
    # Traer primero lo que otro ordenador haya subido a la web
    guardar("proyectos-web", RAIZ, "Actualiza la web de proyectos")
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
    if choques:
        avisar()


if __name__ == "__main__":
    main()
