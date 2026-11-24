# Web de proyectos

Una web sencilla para ver de un vistazo todos los proyectos: qué son, en qué punto están, qué falta y cómo retomarlos.

## Cómo funciona

Cada proyecto es una carpeta dentro de `fichas`, con dos archivos que se escriben a mano (o se le piden a Claude):

- `ficha.json`: nombre, estado, avance, etapas, lo hecho, lo pendiente, diario y lecciones.
- `retomar.md`: la memoria larga para ponerse al día.

`generar.py` lee las fichas y escribe la web: `index.html` y una página por proyecto en la carpeta `p`.

## Órdenes

- `python generar.py`: rehace la web.
- `python generar.py nuevo mi-proyecto`: crea la ficha vacía de un proyecto nuevo.
- `publicar.bat`: rehace la web y la sube a GitHub.
- `python copia.py`: guarda una copia de seguridad de cada proyecto en OneDrive.
- `python guardar.py`: guarda en git y sube a GitHub lo que haya cambiado en los proyectos de `local.json`, y pone al día la web. Lo que hace queda en `guardar.log`.

## Lo que va solo en el ordenador principal

Dos tareas programadas de Windows:

- «Guardar proyectos»: ejecuta `guardar.py` cada dos horas.
- «Copia de proyectos»: ejecuta `copia.py` cada domingo a las doce.

Las memorias de cada ficha no se escriben solas: hay que actualizarlas a mano o pedírselo a Claude.

## Estados que entiende

`activo`, `pausado`, `estancado`, `terminado` e `idea`.

## Archivos de cada ordenador

- `config.json`: título de la web y nombre de usuario de GitHub. Se comparte.
- `local.json`: dónde está en este ordenador el código de cada proyecto. No se sube, porque cada ordenador tiene sus rutas. Si un proyecto consta ahí, la web mide sola sus líneas de código y su último cambio.

## Añadir un proyecto desde otro ordenador

1. Clonar este repositorio.
2. `python generar.py nuevo nombre-del-proyecto` y rellenar la ficha.
3. Crear `local.json` con la ruta del código, si se quiere que se mida solo.
4. `publicar.bat`.
