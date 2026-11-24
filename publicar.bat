@echo off
rem Rehace la web con las fichas de ahora y la sube a GitHub.
cd /d "%~dp0"
rem Primero se trae lo que otro ordenador haya subido.
git pull --rebase --autostash
if errorlevel 1 (
    git rebase --abort >nul 2>nul
    echo No se ha podido traer lo que hay en GitHub. No subo nada.
    pause
    exit /b 1
)
python generar.py
if errorlevel 1 (
    echo La web no se ha podido generar. No subo nada.
    pause
    exit /b 1
)
git add -A
git diff --cached --quiet
if not errorlevel 1 (
    echo No hay cambios que subir.
    pause
    exit /b 0
)
git commit -m "Actualiza la web de proyectos"
git push
if errorlevel 1 (
    echo No se ha podido subir. Mira el mensaje de arriba.
) else (
    echo Subido. La web tarda un minuto o dos en verse cambiada.
)
pause
