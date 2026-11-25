## Qué es y qué se busca

Un asistente de voz personal, gratuito y sin servicios de pago. Se dice «hey Jarvis» al móvil Android, se da una orden y la respuesta suena por el auricular. La meta es poder manejar de viva voz, sin mirar la pantalla, los mensajes, el correo, los archivos, el móvil y el ordenador.

Tiene dos piezas. El **cliente** va en el móvil, dentro de Termux: escucha sin parar, pero el audio no sale del móvil hasta que oye la palabra de llamada. El **servidor** va en un ordenador encendido: pasa la voz a texto, pregunta a una IA, ejecuta la orden y devuelve la respuesta hablada.

## Normas del proyecto

- **No inventar.** Si Jarvis no sabe algo o no puede averiguarlo, lo dice.
- **Todo gratuito.** Solo IA y servicios sin coste; las claves van en variables de entorno, nunca en archivos.
- **Lo delicado se confirma de viva voz.** Enviar, borrar, apagar o llamar piden un «sí».
- **Nada se destruye.** Lo borrado y las versiones anteriores van a una papelera propia.
- **Jarvis propone, no se cambia solo.** Escribe propuestas de mejora; aplicarlas es cosa de una persona, y hay que revisarlas antes.
- **Pruebas sin tocar lo real.** Servidor de prueba en otro puerto, WhatsApp, correo, casa y teléfono de mentira.
- **Gastar pocos tokens.** Medir antes de alargar las instrucciones a la IA.

## Cómo ponerlo en marcha

El servidor, en Windows: `servidor\arrancar.ps1`. En Linux: `servidor/instalar_servidor.sh` y luego `servidor/arrancar.sh`. Al arrancar dice la dirección y la contraseña que hay que poner en el móvil. El entorno de Python del proyecto es de la versión 3.12, porque una de las piezas no existe para versiones más nuevas.

El panel de control se abre en el navegador, en `/panel` del servidor, o con `servidor\abrir_panel.ps1`.

El móvil: instalar Termux y Termux API, ejecutar `instalar_termux.sh` y después `python cliente.py`. La primera vez pregunta la dirección del servidor y la contraseña. Para ponerlo al día, `bash actualizar.sh` en la carpeta del cliente; el cliente dice su versión al arrancar.

Otras órdenes útiles:

- `python cliente.py --conexion`: comprueba paso a paso si el móvil llega al servidor.
- `python cliente.py --fuera DIRECCIÓN`: guarda la dirección para usarlo fuera de casa.
- `python entrenar.py`: graba la voz del dueño y entrena su detector; con `--repasar` reentrena con las activaciones falsas.
- `servidor\clave_ia.ps1`: guarda la clave de un servicio de IA y la prueba.
- `python catalogo.py`: dice qué IA hay y si contestan.
- `servidor\comprobar_conexion.ps1`: revisa la red desde el ordenador.

Las variables de entorno que cambian el comportamiento empiezan todas por `JARVIS_`. Las instrucciones completas están en `LEEME.md`.

## Cómo está hecho

Python en las dos piezas. El servidor es una aplicación FastAPI con un canal en directo para la voz y otro para el panel.

Cliente (`cliente`):

- `cliente.py`: escucha, graba la orden, la envía y reproduce la respuesta. También vigila para poder interrumpir.
- `palabra_clave.py`: el detector de la palabra de llamada. `entrenar.py`: el modelo de la voz del dueño.
- `manos.py`: lo que el móvil hace cuando el servidor se lo pide (abrir aplicaciones, pulsar, leer la pantalla).
- `app_movil.py`: la pantalla instalable del móvil.

Servidor (`servidor`):

- `servidor.py`: el centro. Arranca todo, atiende al móvil y al panel, lleva la conversación y reparte cada orden.
- `comun.py`: lo compartido (las piezas cargadas y el estado de la conversación). `ordenes.py`: las instrucciones que se mandan a la IA y cómo se interpreta su respuesta.
- Los que atienden cada tipo de orden: `en_archivos.py`, `en_internet.py`, `en_correo.py`, `en_whatsapp.py` y `en_aparatos.py`.
- Las IA: `cerebro.py` (fila con relevo), `catalogo.py` (servicios y modelos), `cupos.py` (cuenta de lo gastado), `selector.py` (cuál conviene a cada petición), `pulso.py` (cuál va rápida ahora), `equipo.py` (qué modelos locales caben).
- Oír y hablar: `oido.py`, `voz.py`, `vocabulario.py` y `entrenamiento.py`.
- WhatsApp: `whatsapp.py`, `mensajes.py` (lo recibido, en una base de datos) y `conversaciones.py` (contarlo de viva voz).
- `correo.py`, `alarmas.py`, `internet.py` e `investigador.py`.
- Archivos: `archivos.py`, `explorador.py`, `lector.py`, `taller.py` y `guardian.py`.
- `movil.py` y `pc.py`: las órdenes para el móvil y para el ordenador.
- `memoria.py`: lo que sabe del dueño. `conciencia.py`: lo que sabe de sí mismo, con las listas de lo que sabe y no sabe hacer.
- `panel.html`, `valoraciones.py` y `tareas.py`: el panel de control.

La IA no hace nada por sí misma: contesta con una orden en una línea, como `WHATSAPP|contacto|mensaje` o `ALARMA|cuándo|mensaje`, y es el programa quien la ejecuta. Al añadir una función real hay que apuntarla en la lista de capacidades de `conciencia.py` y en `tareas.py`.

Las dependencias van en una sola dirección: `servidor.py` usa los módulos `en_`, estos usan las piezas, y ningún módulo importa a `servidor.py`. El archivo `ESQUEMA.md` del proyecto lo explica entero y trae un mapa de todos los archivos, que escribe `pruebas\mapa.py`.

Pruebas (carpeta `pruebas`): `todas.py` no usa Internet ni toca nada real y tarda menos de un minuto. Para probar de punta a punta con las IA de verdad, `servidor_de_prueba.py` (puerto 8011, con casa, ordenador, correo y teléfono de mentira) y `hablar.py`, que manda frases escritas y dice qué orden dio la IA.

Fuera del repositorio quedan, a propósito: los modelos descargados, las grabaciones, la contraseña, la sesión de WhatsApp, los mensajes guardados y los logotipos del panel. Los modelos se bajan solos al arrancar.

## Dónde está ahora

- La voz de ida y vuelta funciona en el móvil real: activación, orden y respuesta.
- En el móvil real también funcionan «abre YouTube» y «pon tal cosa en YouTube».
- Las claves de varios servicios de IA gratuitos están puestas y contestan.
- La cuenta de correo propia de Jarvis existe y el inicio de sesión funciona.
- Tailscale está instalado en el ordenador y en el móvil.
- Casi todo lo demás está escrito y probado solo con simulaciones.
- El cliente va por la versión «20 de noviembre, décima».
- El 25 de noviembre de 2026 el servidor se repartió en módulos. Se comprobó con las pruebas y de punta a punta con servicios de mentira; WhatsApp, que nunca se prueba con la sesión real, es lo único que no se ha visto funcionar después del reparto.

## Qué falta

1. Probar en real lo simulado: WhatsApp recibido y notas de voz, alarmas en el móvil, interrumpir, pantalla del móvil, mandos de reproducción, pasar fotos y archivos, llamadas y SMS, envío de correo, y el uso en la calle.
2. El botón del reloj: falta que una aplicación de automatización del móvil capture el botón y llame a la puerta local del cliente.
3. Un servidor siempre encendido.
4. Funciones apuntadas como pendientes en la pestaña de tareas: contestar correos, buscar fotos por lo que se ve, decir dónde está el móvil, cerrar programas y escribir en el ordenador lo dictado.
5. Reconocer quién habla. La idea es entrenar un reconocedor con las grabaciones ya valoradas.
6. Reordenar `LEEME.md` por temas, que ha crecido por capas. En `servidor.py` aún quedan el reparto de las órdenes y las direcciones del panel.

## Cómo se depura

1. Leer `modelos\jarvis.log`: dice los tiempos de cada orden y qué IA contestó.
2. Leer `modelos\diagnostico\registro.txt`: es el registro que sube el móvil, con activaciones, falsos y tiempos.
3. Si falla el oído, mirar `modelos\fallos_de_oido` y medir con esos audios antes de cambiar nada.
4. Si el dueño dice «mira el informe», leer `modelos\informe_no_sabe.md`.
5. Si el móvil no conecta, comprobar primero qué versión del cliente lleva.

## Cosas técnicas que costó averiguar

- El detector general de la palabra falla con acento castellano. Por eso hay un modelo propio de la voz del dueño.
- En Termux no entra el paquete del detector; se usan sus modelos directamente con numpy y onnxruntime.
- El reconocedor de voz escribe mejor la orden si se le corta antes el «hey Jarvis» y se le pasa sin pista.
- Los servicios gratuitos cambian: unos piden tarjeta, otros se saturan. `catalogo.py` pregunta a cada uno qué modelos tiene de verdad.
- Para saber si una IA va rápida vale más el tiempo de las preguntas reales que una sonda mínima.
- Termux no recibe los botones multimedia del reloj. De ahí la puerta local para una aplicación de automatización.
- El móvil solo conecta al dar una orden, así que pregunta cada pocos segundos si hay avisos o alarmas vencidas.
- No hay ffmpeg en el ordenador: las notas de voz se convierten con otra biblioteca de Python.
- El buscador solo contesta bien con una identificación de navegador sencilla.
