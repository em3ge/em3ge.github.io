## Qué es y qué se busca

Un programa que juega solo aventuras gráficas de Sierra dentro de ScummVM. La meta no es acabar un juego concreto, sino tener un jugador que sirva para cualquiera: explora, lee una guía, la sigue y aprende las mecánicas por su cuenta.

Se resuelve de forma orgánica: explorar el mapa, avanzar en el juego, volver a explorar cuando haga falta, y así hasta el final.

## Normas del proyecto

Estas normas se han ido fijando por el camino y siguen en pie.

- **Todo genérico.** Nada escrito a mano para un juego concreto. Cada atasco se arregla como clase de problema.
- **Pasos cortos y firmes.** No se abre una etapa nueva hasta dar por buena la anterior.
- **Nunca cargar una partida para viajar.** Solo se guarda donde consta que se llegó andando.
- **Saltos solo legales.** Se puede saltar entre salas ya andadas y colocarse dentro de una sala si hay camino. A una sala nueva se entra siempre andando.
- **Rapidez.** Los puntos son la señal de avance. Nada de paseos lentos ni de repetir lo que ya falló con la partida igual.
- **Pruebas cortas.** Pocos minutos y pocos pasos, y sobre una copia de la partida, nunca sobre la buena.

## Cómo ponerlo en marcha

Hace falta Windows, Python 3 con los paquetes de `requirements.txt`, ScummVM, una carpeta de juegos con una subcarpeta por juego, y una clave de Gemini en la variable de entorno `GEMINI_API_KEY`.

- `abrir.bat` abre la ventana. El botón Empezar sigue la guía si ya hay plan; si no, prepara y explora.
- `probar.bat 10 3` hace una prueba de diez minutos y tres pasos. El resumen queda en `datos\ultima_prueba.txt`.
- `parar.bat` pide parar por las buenas.
- `desde_cero.bat` aparta lo explorado a `copias` y empieza de nuevo.

Desde la línea de órdenes: `python aventura.py` seguido de `preparar`, `explorar`, `jugar MINUTOS PASOS`, `ir SALA`, `donde` o `mapa`.

Todo lo que el programa dice queda en `datos\diario.txt`. Es lo primero que hay que leer para depurar.

## Cómo está hecho

Algo más de 9000 líneas de Python.

- `aventura.py`: las órdenes. `interfaz.py`: la ventana, con el juego metido dentro y pestañas de guía, mapa, registro y ajustes.
- `nucleo/enlace.py`: habla con ScummVM. `nucleo/sci.py`: el motor de Sierra, por el depurador. `nucleo/memoria.py`: lee la memoria del juego, sin escribir nunca.
- `nucleo/partida.py`: no atascarse, carteles, puntos seguros. `nucleo/terreno.py`: por dónde se pisa. `nucleo/viaje.py`: andar, cruzar, explorar, saltar. `nucleo/mapa.py`: el mapa y su dibujo.
- `nucleo/guias.py` y `nucleo/lugares.py`: bajan guías y casan sus lugares con las salas. `nucleo/plan.py`: la IA convierte la guía en pasos.
- `nucleo/jugar.py`: el jugador, la pieza más grande. `nucleo/mecanica.py`: aprende mecánicas. `nucleo/rumbo.py`: revisa el rumbo, repesca pasos y llama a la IA de emergencia.
- `nucleo/ia.py`: Gemini, y OpenAI u Ollama si los hay. `nucleo/opciones.py`: los ajustes del resolvedor.
- `nucleo/grabadora.py` e `imagenes.py`: los vídeos de las muertes.

Los datos de cada juego viven en `datos\<juego>\`: `catalogo.json` (lo que el juego declara), `mapa.json` y `mapa.png`, `plan.json`, `jugar.json` (el estado de la partida y todo lo aprendido), `aprendido.json`, `carteles.json`, las guías y las partidas guardadas.

## Dónde está ahora

Juego de prueba: Leisure Suit Larry 3.

- Mapa: 34 salas pisadas.
- Guía: paso 86 de 132. Han salido bien 58 pasos. 1587 puntos.
- Acaba de terminar la parte de Larry y empieza la de Patti.

## Qué falta

1. La parte de Patti, pasos 86 a 132.
2. Pasos pendientes del hotel: el 79 (salir del hotel) y del 66 al 68 (estudio de aeróbic, sala 390, 99 puntos). Allí no aparece el personaje que la guía espera y no se sabe qué condición falta.
3. Fallos conocidos: el ascensor y la cerradura (salas 460 y 470) dan por bueno lo que no lo es; tras un paso hecho sentado, el siguiente se teclea sin levantarse; la sala 380, a la que se entra por una orden, gasta cinco minutos buscando puertas; el aviso de guardar estorba; el juego se cerró una vez sin causa conocida.
4. La IA potente gratuita casi nunca tiene cupo. Decidir si se paga un modelo o se usa uno local.

## Cómo se depura

1. Leer el final de `datos\diario.txt`.
2. Copiar `datos\<juego>` a una carpeta de pruebas y cambiar `savepath` en su `scummvm.ini`. Nunca abrir el juego sobre la carpeta buena: dos ScummVM sobre la misma partida la estropean.
3. Probar con pocos minutos y pocos pasos.
4. Vigilar `plan.json` después de cada prueba: las correcciones automáticas de sala pueden estar mal.
5. Si una sesión avanzó en falso, `rebobinar.py` devuelve el plan a un paso anterior.

Interruptores para pruebas, como variables de entorno: `AVENTURA_SIN_MEMORIA`, `AVENTURA_SIN_VIDEO`, `AVENTURA_LENTO`, `AVENTURA_ANDANDO`, `AVENTURA_IA_POTENTE` y `AVENTURA_PRUEBA`.

## Cosas técnicas que costó averiguar

- El depurador de ScummVM se abre con Control, Alt y D. Hay que comprobar por la imagen que está abierto antes de teclear: una tecla que se cuela al juego pulsa el botón de un cartel.
- Teclear más deprisa de doce milésimas por letra pierde letras.
- Variables del motor: la 0 es el personaje, la 11 la sala, la 15 los puntos.
- `dissect_script` da las salidas de todas las salas sin visitarlas. Todo el juego en minuto y medio.
- `show_map 2` enseña por dónde se puede pisar.
- `room N` hace que el juego cambie de sala por sus propios medios. Hay tramos donde devuelve al personaje; esos se andan siempre.
- Dentro de una misma sala el juego puede cambiar qué colores del suelo están prohibidos. Hay un terreno por cada caso.
- Minimizar la ventana dejaba ciego al programa, que mira la imagen. Ahora el juego se suelta y queda debajo.
- La clave gratuita de Gemini da unas veinte consultas al día por modelo en los grandes. Se reparte entre varios.
