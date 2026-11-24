@echo off
rem Rehace la web con las fichas de ahora y la sube a GitHub.
cd /d "%~dp0"
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
