## Qué es y qué se busca

Llavero es un gestor de contraseñas para Android que no pide ningún permiso, así que no puede conectarse a Internet. Nació al ordenar las llaves de firma de las aplicaciones que se van a publicar en Google Play: hacía falta un sitio seguro para esas llaves y, ya puestos, para las contraseñas corrientes. La idea de partida fue una página web sin conexión; se cambió a una aplicación aislada, «tipo cartera de bitcoin», con exportar e importar protegidos por la contraseña maestra.

## Normas del proyecto

- **Ni un permiso, ni una biblioteca.** `construir.ps1` se para si el manifiesto pide un permiso o el código nombra clases de red.
- **El formato del archivo no se cambia sin subirle la versión** (`llavero-1`). Lo leen tres programas: la aplicación, la página web y la herramienta del ordenador.
- **No dar por bueno lo que no se ha probado en el móvil.**
- **La contraseña maestra solo la teclea el dueño.** No se pide, no se apunta y no se pasa por la línea de órdenes.
- **Antes de cambiar la llave de firma de la aplicación, exportar.** Cambiarla obliga a desinstalar y al desinstalar se pierde el llavero del móvil.

## Cómo ponerlo en marcha

En PowerShell, en la carpeta del proyecto:

1. `.\construir.ps1` fabrica `salida\llavero.apk` con el JDK y el SDK de la carpeta de datos locales, los mismos de volumen-nocturno.
2. `adb install -r salida\llavero.apk` con el móvil enchufado.
3. `.\pruebas\cruzada.ps1` pasa las pruebas del cifrado (necesita Edge).
4. `.\meter_llaves.ps1` empaqueta las llaves de firma de la carpeta `llaves` de Documentos en un archivo cifrado para importar en el móvil.

La llave con la que se firma la aplicación está fuera del proyecto, en la carpeta central de llaves, subcarpeta `llavero`.

## Cómo está hecho

- `Cofre.java`: el cifrado, sin nada de Android. PBKDF2-HMAC-SHA-256 con 600 000 vueltas y sal de 16 bytes; AES-256-GCM con iv de 12 bytes nuevo en cada guardado; la cabecera (formato, vueltas y sal) va como dato autenticado. Lee la cabecera con expresiones regulares para no depender de ninguna biblioteca de JSON.
- `MainActivity.java`: una sola actividad con tres pantallas hechas por código. El llavero abierto vive en memoria (`boveda`, `clave`, `sal`, `iteraciones`) y se pone a `null` al cerrar. Guardar escribe a un archivo aparte y lo renombra. `onStop` cierra el llavero salvo que haya un selector de archivos abierto (`eligiendo`).
- Importar: sin llavero en el móvil, la copia pasa a ser el llavero con su misma contraseña. Con llavero abierto, se mezclan por `id` y gana lo de `cambiado` más reciente.
- `pc\Empaquetar.java`: una entrada de tipo `llave` por cada subcarpeta con archivos `.jks`; el `id` es `llave-` más el nombre de la carpeta, para que repetir la importación ponga al día y no duplique.
- `web\index.html`: el mismo formato con Web Crypto, con política de contenido que impide cualquier conexión.

## Estado al acabar el 26 de noviembre de 2026

- Probado en el ordenador: cifrado de Java, cifrado de la página, cruce en los dos sentidos y la herramienta de las llaves con datos de mentira.
- Sin probar: toda la aplicación en un móvil. Lo primero al retomar es instalarla y recorrerla entera: crear, añadir, adjuntar, exportar, importar, mezclar, cambiar la contraseña maestra, el cierre solo y el botón de atrás.
- Dudas que mirar en el móvil: que el teclado no tape los campos, que los cuadros de diálogo se lean bien y que el selector de archivos no cierre el llavero.

## Ideas para más adelante

- Abrir con la huella, guardando la clave en el almacén seguro del móvil.
- Servicio de autorrelleno para otras aplicaciones.
- Argon2 en lugar de PBKDF2.
