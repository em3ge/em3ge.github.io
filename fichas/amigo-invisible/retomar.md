## Qué es y qué se busca

La aplicación se llama **MisteryFriend** (así lo escribió el dueño; en inglés correcto sería «Mystery»). La carpeta, el repositorio (`em3ge/amigo-invisible`, privado), el paquete (`io.github.em3ge.amigoinvisible`) y la dirección web (`/amigo-invisible/`) llevan un nombre neutro para poder cambiar el nombre sin romper nada. Antes se llamó RegalON durante unas horas.

Es un amigo invisible: quien organiza crea la sesión en la aplicación; su código es una palabra graciosa del diccionario con dos números (Zascandil27) y va en un QR; cada participante se apunta con nombre, correo, idea de regalo y comentario, y confirma el correo con un código de 4 números (al principio iba a ser un Pokémon; el dueño lo cambió); quien organiza pone exclusiones y sortea; a cada uno le llega su resultado por correo.

## Normas del proyecto

- **Privacidad** (la pidió el dueño): quien organiza no ve correos (tapados), nadie ve el reparto, nadie puede averiguar si un correo está apuntado, borrado a los 90 días.
- **Un solo permiso (Internet) y ninguna biblioteca.**
- **Las reglas viven en el servidor**, con su prueba en `pruebas/servidor.html`.
- **No dar por bueno lo que no se ha probado** en el móvil y contra el servidor de verdad.

## Cómo ponerlo en marcha

1. Servidor: `servidor\PUBLICAR.md` (lo hace el dueño con su cuenta de Google; se le recomendó una cuenta aparte, por ejemplo la de Jarvis).
2. `.\construir.ps1` (necesita `servidor\direccion.txt` con la dirección /exec).
3. `.\publicar_web.ps1` sube la página, la política, la aplicación y `.well-known\assetlinks.json` a esta web.
4. Pruebas: `pruebas\servidor.ps1`, `pruebas\web.ps1`, `pruebas\qr.ps1`.

## Estado al acabar el 27 de noviembre de 2026

Versión 1.0 (código 1). Probado en el ordenador: el servidor con Google imitado (45 de 45), la página web recorrida como participante (10 de 10) y el QR contra la biblioteca qrcode (56 de 56). La aplicación compila y se firma, pero **no se ha abierto en ningún móvil** (no estaba enchufado) y **el servidor no está publicado**: nada se ha probado contra Google de verdad ni se ha mandado un correo real.

Preparado para Google Play en la carpeta `play` (empezar por `play\pasos.md`); faltan las capturas y la parte de la cuenta.
