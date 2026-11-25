## Qué es y qué se busca

Chitón es una aplicación de Android que suaviza los picos de volumen de lo que suena en el móvil. Nació de un caso concreto: dormirse con un programa de humor puesto y que los aplausos, mucho más altos que la voz, no despierten. La idea de partida era que la aplicación «viera el futuro» y bajara el volumen antes del pico.

La carpeta y el repositorio se llaman `volumen-nocturno`; «Chitón» es el nombre de la aplicación.

## Normas del proyecto

- **No dar por bueno lo que no se ha probado en el móvil.** Compilar no es probar. Con el teléfono enchufado se instala, se pulsa, se leen el registro y las capturas.
- **Dejar el móvil como estaba.** El modo anticipado silencia la música y sujeta el volumen de la alarma; al apagar, y también tras un cierre brusco, los dos vuelven a su sitio. Al reinstalar con el modo encendido hay que comprobarlo.
- **Sin bibliotecas añadidas.** Solo lo que trae Android, para que el paquete se pueda fabricar con el guion propio.
- **Textos claros y botones con descripción**, para que se pueda usar sin mirar la pantalla.

## Cómo ponerlo en marcha

En PowerShell, dentro de la carpeta del proyecto:

1. Una sola vez, `preparar_herramientas.ps1`: descarga Java 17 y las piezas mínimas de Android a la carpeta de datos locales del usuario. No hace falta Android Studio ni permisos de administrador.
2. `construir.ps1`: fabrica `salida\volumen-nocturno.apk`. El número de versión está dentro de ese guion.
3. Con el móvil enchufado y la depuración USB activada: `adb install -r salida\volumen-nocturno.apk`.

La clave de firma se crea sola la primera vez en la carpeta `firma`, que no se sube a GitHub. Si se pierde, para instalar una versión nueva hay que desinstalar antes la aplicación.

## Cómo está hecho

Cuatro archivos Java en `src`, sin dependencias, para Android 9 o posterior (el modo anticipado pide Android 10).

- `ServicioCalma.java`: el motor. Un servicio en primer plano con los dos modos.
  - Directo: un efecto `DynamicsProcessing` (compresor de una banda y limitador) sobre la sesión de audio 0, que es la salida general. Un `Visualizer` mide el nivel diez veces por segundo.
  - Anticipado: pide permiso de captura (`MediaProjection`), graba el sonido de las otras aplicaciones con `AudioRecord`, lo guarda en una cola de tramos de 20 milisegundos y lo emite con retraso por un `AudioTrack` del canal de alarma. Para cada tramo que sale mira los siguientes (hasta tres décimas) y va bajando la ganancia antes de que llegue el pico.
  - Los dos aprenden el nivel de la «voz normal» (función `aprender`): el nivel que el sonido solo ha superado una cuarta parte del tiempo en el último minuto. El umbral va unos decibelios por encima, según la fuerza elegida (tabla `NIVELES`). El anticipado mide sin los graves y decide con el nivel sostenido de las últimas tres décimas, para que una sílaba fuerte no cuente como pico.
  - Los dos apuntan en una «historia» lo que suena y lo que recortan; de ahí sale la gráfica.
- `MainActivity.java`: la pantalla, hecha por código, sin archivos de diseño.
- `Grafica.java` y `Medidor.java`: la gráfica y la barra de bajada.

El volumen en el modo anticipado: se silencia el canal de música, para no oír el original, sin mover su paso. Chitón suena tan alto como sonaría la música en ese paso. Las teclas del móvil siguen funcionando porque Chitón escucha los cambios de volumen de dos canales: el de música (cuando hay un vídeo sonando) y el de alarma (cuando no lo hay, este móvil manda ahí las teclas). La alarma se sujeta un paso por debajo del máximo para notar subidas y bajadas.

## Dónde está ahora

Versión 1.7, instalada en el móvil del dueño (Android 16).

La 1.6 se probó de oído y el dueño no notó que bajara los aplausos ni la música alta. Hubo dos causas. La primera se vio con `pruebas/simular.py`: se bajaba la voz, sílaba a sílaba, tanto como los picos. La segunda salió al medir en el móvil con una charla real: si el vídeo empezaba flojo, se tomaba por voz normal un nivel demasiado bajo y se le quitaban unos 20 decibelios a la propia voz.

La 1.7 corrige las dos. Medida en el móvil con esa charla (registro propio, minuto y medio): la voz normal se asienta en unos diez segundos, la voz queda sin tocar y las risas del público bajan entre 4 y 7 decibelios. Falta la prueba de oído del dueño con sus programas.

Lo que sigue se comprobó con la 1.6.

Comprobado en el móvil real, con capturas de pantalla, el registro del teléfono y pulsaciones simuladas por cable:

- El modo anticipado captura el sonido de su YouTube con la música silenciada.
- La gráfica enseña el pico por venir y el recorte.
- Las teclas de volumen suben y bajan el volumen de Chitón, con vídeo y sin él.
- Al cerrar de golpe y volver a abrir, la música y la alarma vuelven a como estaban.

Sin comprobar:

- Que la 1.7 se note de oído con los programas del dueño. Con la charla de prueba las risas solo pasaban 2 o 3 decibelios del umbral; unos aplausos fuertes deberían bajar más, pero no se ha medido.
- Que el modo anticipado suene limpio, sin doble sonido ni cortes, y que el directo recorte en este móvil.
- El retraso real del modo anticipado: a la ventaja elegida se suma lo que tarda el teléfono en capturar y emitir, y eso no está medido.

## Qué falta

1. La prueba de oído del dueño con el botón «Comparar», y afinar con eso los tres niveles de fuerza.
2. Los diez primeros segundos de un vídeo: mientras se asienta la voz normal, baja de más.
2. Medir el retraso propio del móvil y, si es grande, descontarlo de la ventaja.
3. Botón en los ajustes rápidos.
4. Decidir qué hacer con auriculares: el canal de alarma suena también por el altavoz.
5. Apagado automático a una hora.

## Cómo se depura

Con el móvil enchufado:

- `adb logcat -s Chiton:I`: el registro propio. Cada cinco segundos dice el nivel capturado, el habitual, lo que baja y, de esos cinco segundos, lo más que se pasó del umbral y la mayor bajada; y apunta cada tecla de volumen y el volumen resultante.
- `python pruebas/simular.py`, en el ordenador: repite las cuentas del motor con una señal fabricada de voz y aplausos. Las cuentas están copiadas a mano de `ServicioCalma.java`: si se cambian allí, hay que cambiarlas en el guion.
- `adb shell dumpsys audio`: el estado de cada canal de volumen (silenciado o no, y su paso) y qué aplicaciones están sonando.
- `adb shell input keyevent 24` y `25`: simulan subir y bajar volumen.
- `adb shell screencap` y `adb pull`: una captura de la pantalla para ver la gráfica.
- `adb shell dumpsys package <paquete>`: dice si una aplicación deja capturar su sonido (`ALLOW_AUDIO_PLAYBACK_CAPTURE`).

## Cosas técnicas que costó averiguar

- Desde otra aplicación no se puede retrasar el vídeo: cuanta más ventaja se da al sonido, más desfase con la imagen. Por eso la ventaja es ajustable.
- Con el canal de música silenciado, la tecla de bajar cambia el paso sin quitar el silencio, y la de subir lo quita. El paso real solo se conoce por el aviso de cambio de volumen que difunde Android, porque la consulta normal devuelve cero mientras está silenciado.
- Android pide de nuevo el permiso de captura cada vez que se enciende el modo anticipado; no se puede guardar.
- El servicio tiene que declararse de tipo «proyección» además de «reproducción», y ponerse en primer plano antes de pedir la captura.
- Las aplicaciones que prohíben la captura (suelen ser las de música y vídeo de pago) llegan como silencio. No hay forma de distinguirlo de una pausa: Chitón avisa y no cambia de modo solo.
- Los guiones de PowerShell van sin acentos a propósito: PowerShell 5 los estropea en archivos sin marca de codificación.
