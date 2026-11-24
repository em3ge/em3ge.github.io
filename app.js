// Buscador, filtros por estado, "hace cuanto" y boton de copiar. Sin esto la pagina se lee igual.
(function () {
  var AVISO_DIAS = 30;

  function dias(iso) {
    var p = (iso || "").split("-");
    if (p.length < 3) return null;
    var f = new Date(+p[0], +p[1] - 1, +p[2]);
    var hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    return Math.round((hoy - f) / 86400000);
  }

  function hace(n) {
    if (n === null || n < 0) return "";
    if (n === 0) return "hoy";
    if (n === 1) return "ayer";
    if (n < 60) return "hace " + n + " días";
    return "hace " + Math.round(n / 30) + " meses";
  }

  document.querySelectorAll("[data-fecha]").forEach(function (caja) {
    var n = dias(caja.getAttribute("data-fecha"));
    var hueco = caja.querySelector(".hace");
    if (!hueco || n === null) return;
    var activo = caja.getAttribute("data-estado") === "activo";
    if (activo && n >= AVISO_DIAS) {
      hueco.textContent = "· sin tocar " + hace(n);
      hueco.classList.add("aviso");
    } else {
      hueco.textContent = "· " + hace(n);
    }
  });

  var tarjetas = Array.prototype.slice.call(document.querySelectorAll(".tarjeta"));
  var buscar = document.getElementById("buscar");
  var cuantos = document.getElementById("cuantos");
  var botones = Array.prototype.slice.call(document.querySelectorAll(".filtro"));
  var estado = "";

  function sinTildes(t) {
    return t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function aplicar() {
    var q = sinTildes(buscar ? buscar.value.trim() : "");
    var n = 0;
    tarjetas.forEach(function (t) {
      var ve = (!estado || t.getAttribute("data-estado") === estado) &&
               (!q || sinTildes(t.getAttribute("data-texto") || "").indexOf(q) !== -1);
      t.hidden = !ve;
      if (ve) n++;
    });
    if (cuantos) {
      cuantos.textContent = n === tarjetas.length
        ? ""
        : (n === 0 ? "Ningún proyecto coincide." : "Se ven " + n + " de " + tarjetas.length + " proyectos.");
    }
  }

  if (buscar) buscar.addEventListener("input", aplicar);
  botones.forEach(function (b) {
    b.addEventListener("click", function () {
      estado = b.getAttribute("data-estado");
      botones.forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
      aplicar();
    });
  });

  document.querySelectorAll("[data-copiar]").forEach(function (b) {
    b.addEventListener("click", function () {
      var origen = document.getElementById(b.getAttribute("data-copiar"));
      var aviso = document.getElementById("copiado");
      if (!origen) return;
      function dicho(t) { if (aviso) aviso.textContent = t; }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(origen.textContent).then(
          function () { dicho("Copiado."); },
          function () { dicho("No se pudo copiar. Selecciona el texto a mano."); });
      } else {
        dicho("Este navegador no deja copiar. Selecciona el texto a mano.");
      }
    });
  });
})();
