# Web de proyectos

Una web sencilla para ver de un vistazo todos los proyectos: qué son, en qué punto están, qué falta y cómo retomarlos.

## Cómo funciona

Cada proyecto es una carpeta dentro de `fichas`, con dos archivos que se escriben a mano (o se le piden a Claude):

- `ficha.json`: nombre, estado, avance, etapas, lo hecho, lo pendiente, diario y lecciones.
- `retomar.md`: la memoria larga para ponerse al día.

Dos cosas más, opcionales, hacen la página de cada proyecto más vistosa:

- `portada.svg` (o `.jpg`, `.png`, `.webp`) dentro de la carpeta de la ficha: la imagen del proyecto, apaisada, de 1200 por 675. Si falta, `generar.py` dibuja una sencilla.
- En `ficha.json`, `"color"` (el color del proyecto, como `"#5eead4"`) y `"esquema"`, el dibujo de la estructura del programa:
  - `"grupos"`: cajas con nombre. Cada una lleva `"columna"` (1, 2, 3… de izquierda a derecha; dos grupos con la misma columna se apilan) y sus `"elementos"`, cada uno con `"id"`, `"nombre"`, `"detalle"` y, si se quiere resaltar, `"destacado": true`. Nombres y detalles cortos, de unas 25 letras.
  - `"conexiones"`: flechas, con `"de"` y `"a"` (los `id`), y opcionales `"texto"`, `"fuerte": true` (línea de trazos de color) y `"doble": true` (flecha en los dos sentidos). Quedan mejor entre columnas vecinas.

- En `ficha.json`, `"muestra"`: una muestra de ejecución real del programa, que sale en su página como «Una muestra de ejecución», con un botón para reproducirla línea a línea. Lleva `"nota"` (de dónde sale y cuándo se grabó), `"papeles"` opcional (cómo se llama cada quien) y `"escenas"`, cada una con `"titulo"` y `"lineas"`; cada línea tiene `"de"` (`tu`, `programa`, `dentro`, `juego` o `nota`) y `"texto"`. Solo debe llevar cosas que hayan pasado de verdad. La de Jarvis se graba con `pruebas\hablar.py` de ese proyecto y la variable `JARVIS_MUESTRA`.

El aspecto de portfolio (titular, presentación, «cómo trabajo») sale de `config.json`.

`generar.py` lee las fichas y escribe la web: `index.html` y una página por proyecto en la carpeta `p`.

## Órdenes

- `python generar.py`: rehace la web.
- `python generar.py nuevo mi-proyecto`: crea la ficha vacía de un proyecto nuevo.
- `publicar.bat`: rehace la web y la sube a GitHub.
- `python copia.py`: guarda una copia de seguridad de cada proyecto en OneDrive.
- `python guardar.py`: guarda en git y sube a GitHub lo que haya cambiado en los proyectos de `local.json`, y pone al día la web. Lo que hace queda en `guardar.log`.

## Lo que va solo en el ordenador principal

Dos tareas programadas de Windows:

- «Guardar proyectos»: ejecuta `guardar.py` al iniciar sesión y cada quince minutos. Guarda lo de este ordenador, trae lo que otro haya subido y sube lo propio. Si el mismo archivo se cambió en dos ordenadores, no pisa nada: deja las dos versiones a salvo y saca una ventana de aviso.

Para que un proyecto esté al día en dos ordenadores, tiene que estar clonado en los dos, constar en el `local.json` de cada uno, y los dos deben tener esta tarea programada.
- «Copia de proyectos»: ejecuta `copia.py` cada domingo a las doce.

Las memorias de cada ficha no se escriben solas: hay que actualizarlas a mano o pedírselo a Claude.

## Estados que entiende

`activo`, `pausado`, `estancado`, `terminado` e `idea`.

## Archivos de cada ordenador

- `config.json`: título de la web y nombre de usuario de GitHub. Se comparte.
- `local.json`: dónde está en este ordenador el código de cada proyecto. No se sube, porque cada ordenador tiene sus rutas. Si un proyecto consta ahí, la web mide sola sus líneas de código y su último cambio.

## Añadir un proyecto desde otro ordenador

1. Clonar este repositorio: `git clone https://github.com/em3ge/em3ge.github.io.git proyectos-web`
2. `python generar.py nuevo nombre-del-proyecto` y rellenar `ficha.json` y `retomar.md` en `fichas\nombre-del-proyecto`.
3. Crear `local.json` con la ruta del código, para que se mida solo y entre en el guardado automático. Ejemplo: `{"nombre-del-proyecto": "C:/Users/yo/Documents/nombre-del-proyecto"}`
4. `publicar.bat`.

En la web pública no deben ir correos, claves ni rutas con nombres de persona.
