"""Genera la web de proyectos a partir de las fichas.

    python generar.py              rehace la web entera
    python generar.py nuevo ID     crea la ficha vacia de un proyecto nuevo (ID sin espacios)

Cada proyecto es una carpeta en fichas\\ID con:
    ficha.json    los datos y las listas (estado, etapas, hecho, pendiente, diario, lecciones)
    retomar.md    la memoria larga para ponerse al dia
    medidas.json  lo escribe este programa si en local.json consta donde esta el codigo

Solo usa lo que trae Python."""
import html
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
FICHAS = RAIZ / "fichas"
SALIDA = RAIZ / "p"

ESTADOS = {
    "activo": "Activo",
    "pausado": "Pausado",
    "estancado": "Estancado",
    "terminado": "Terminado",
    "idea": "Idea",
}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
CODIGO = {".py", ".js", ".ts", ".html", ".css", ".bat", ".ps1", ".c", ".cpp", ".h",
          ".java", ".cs", ".go", ".rs", ".php", ".rb", ".sh", ".sql"}
FUERA = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def leer_json(ruta, defecto=None):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {} if defecto is None else defecto


def e(texto):
    return html.escape(str(texto), quote=True)


def fecha_larga(iso):
    try:
        a, m, d = (int(x) for x in str(iso)[:10].split("-"))
        return f"{d} de {MESES[m - 1]} de {a}"
    except (ValueError, IndexError):
        return str(iso or "")


# ---------- texto con formato sencillo ----------

def en_linea(texto):
    t = e(texto)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    return t


def formato(texto, nivel=3):
    """Titulos (##), listas (- y 1.), parrafos, `codigo` y **negrita**. Nada mas."""
    salida, parrafo, lista = [], [], None

    def cerrar():
        nonlocal lista
        if parrafo:
            salida.append("<p>" + en_linea(" ".join(parrafo)) + "</p>")
            parrafo.clear()
        if lista:
            salida.append(f"</{lista}>")
            lista = None

    for linea in texto.splitlines():
        s = linea.strip()
        if not s:
            cerrar()
            continue
        m = re.match(r"(#{2,4})\s+(.*)", s)
        if m:
            cerrar()
            n = min(6, nivel + len(m.group(1)) - 2)
            ancla = re.sub(r"[^a-z0-9]+", "-", m.group(2).lower()).strip("-")
            salida.append(f'<h{n} id="r-{e(ancla)}">{en_linea(m.group(2))}</h{n}>')
            continue
        m = re.match(r"(-|\d+\.)\s+(.*)", s)
        if m:
            tipo = "ul" if m.group(1) == "-" else "ol"
            if parrafo or lista != tipo:
                cerrar()
                salida.append(f"<{tipo}>")
                lista = tipo
            salida.append("<li>" + en_linea(m.group(2)) + "</li>")
            continue
        if lista:
            cerrar()
        parrafo.append(s)
    cerrar()
    return "\n".join(salida)


# ---------- medir el codigo de un proyecto que este en este ordenador ----------

def git(carpeta, *args):
    try:
        r = subprocess.run(["git", "-C", str(carpeta), *args], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def medir(carpeta):
    carpeta = Path(carpeta)
    if not carpeta.is_dir():
        return None
    lista = git(carpeta, "ls-files", "-z")
    if lista:
        archivos = [carpeta / n for n in lista.split("\0") if n]
    else:
        archivos = [p for p in carpeta.rglob("*")
                    if p.is_file() and not (set(p.relative_to(carpeta).parts) & FUERA)]
    lineas, de_codigo, ultimo = 0, 0, 0.0
    for p in archivos:
        if p.suffix.lower() not in CODIGO:
            continue
        try:
            lineas += p.read_bytes().count(b"\n") + 1
            ultimo = max(ultimo, p.stat().st_mtime)
            de_codigo += 1
        except OSError:
            pass
    m = {"archivos": len(archivos), "archivos_de_codigo": de_codigo, "lineas": lineas,
         "medido": date.today().isoformat()}
    if ultimo:
        m["ultimo_cambio"] = date.fromtimestamp(ultimo).isoformat()
    n = git(carpeta, "rev-list", "--count", "HEAD")
    if n.isdigit():
        m["cambios_guardados"] = int(n)
        m["ultimo_guardado"] = git(carpeta, "log", "-1", "--format=%cs")
    return m


# ---------- cargar ----------

def cargar():
    aqui = leer_json(RAIZ / "local.json")
    proyectos = []
    for carpeta in sorted(FICHAS.iterdir()) if FICHAS.is_dir() else []:
        ficha = carpeta / "ficha.json"
        if not ficha.is_file():
            continue
        try:
            p = json.loads(ficha.read_text(encoding="utf-8"))
        except ValueError as error:
            print(f"OJO: {ficha} tiene un error y no se incluye: {error}")
            continue
        p["id"] = carpeta.name
        if aqui.get(p["id"]):
            m = medir(aqui[p["id"]])
            if m:
                (carpeta / "medidas.json").write_text(
                    json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
            else:
                print(f"OJO: no encuentro la carpeta de {p['id']}: {aqui[p['id']]}")
        p["medidas"] = leer_json(carpeta / "medidas.json")
        try:
            p["retomar"] = (carpeta / "retomar.md").read_text(encoding="utf-8")
        except OSError:
            p["retomar"] = ""
        fechas = [p.get("ultima_actividad", ""), p["medidas"].get("ultimo_cambio", ""),
                  p["medidas"].get("ultimo_guardado", "")]
        fechas += [d.get("fecha", "") for d in p.get("diario", [])]
        p["ultima"] = max(f for f in fechas + [p.get("inicio", "")] if isinstance(f, str))
        proyectos.append(p)
    orden = list(ESTADOS)
    proyectos.sort(key=lambda p: p["ultima"], reverse=True)
    proyectos.sort(key=lambda p: orden.index(p.get("estado")) if p.get("estado") in orden else 9)
    return proyectos


# ---------- piezas de pagina ----------

def cabeza(titulo, descripcion, raiz):
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descripcion)}">
<link rel="stylesheet" href="{raiz}estilo.css">
</head>
<body>
<a class="saltar" href="#contenido">Saltar al contenido</a>
"""


def pie(cfg, raiz):
    return f"""<footer class="pie">
<p>{e(cfg.get('titulo', 'Proyectos'))}. Página actualizada el {fecha_larga(date.today().isoformat())}.</p>
</footer>
<script src="{raiz}app.js"></script>
</body>
</html>
"""


def etiqueta_estado(p):
    est = p.get("estado", "")
    return f'<span class="estado estado-{e(est)}">{e(ESTADOS.get(est, est or "Sin estado"))}</span>'


def barra(p):
    try:
        n = max(0, min(100, int(p.get("avance", 0))))
    except (TypeError, ValueError):
        n = 0
    return (f'<div class="avance"><div class="avance-riel" role="img" aria-label="Avance: {n} por ciento">'
            f'<div class="avance-lleno" style="width:{n}%"></div></div>'
            f'<span class="avance-num" aria-hidden="true">{n} %</span></div>')


def enlaces_codigo(p, cfg):
    usuario, repo = cfg.get("usuario_github", ""), p.get("repositorio", "")
    if not usuario or not repo:
        return ""
    base = f"https://github.com/{usuario}/{repo}"
    rama = p.get("rama", "main")
    nota = ('<p class="nota">El código es privado: GitHub pedirá iniciar sesión con una cuenta que tenga permiso.</p>'
            if p.get("codigo_privado") else "")
    return (f'<div class="botones"><a class="boton" href="{e(base)}">Ver el código</a>'
            f'<a class="boton boton-claro" href="{e(base)}/archive/refs/heads/{e(rama)}.zip">Descargar en zip</a></div>{nota}')


def lista(elementos):
    return "<ul>" + "".join(f"<li>{en_linea(x)}</li>" for x in elementos) + "</ul>"


# ---------- portada ----------

def portada(proyectos, cfg):
    cuenta = {k: sum(1 for p in proyectos if p.get("estado") == k) for k in ESTADOS}
    partes = [cabeza(cfg.get("titulo", "Proyectos"), cfg.get("presentacion", ""), "")]
    partes.append(f"""<header class="cabecera">
<div class="ancho">
<h1>{e(cfg.get('titulo', 'Proyectos'))}</h1>
<p class="presentacion">{e(cfg.get('presentacion', ''))}</p>
</div>
</header>
<main id="contenido" class="ancho">
<section aria-labelledby="t-resumen">
<h2 id="t-resumen" class="oculto">Resumen</h2>
<dl class="cifras">
<div><dt>Proyectos</dt><dd>{len(proyectos)}</dd></div>
""")
    for k, nombre in ESTADOS.items():
        if cuenta[k]:
            partes.append(f"<div><dt>{e(nombre)}s</dt><dd>{cuenta[k]}</dd></div>\n")
    if proyectos:
        ult = max(proyectos, key=lambda p: p["ultima"])
        partes.append(f'<div class="cifra-larga"><dt>Último movimiento</dt><dd>{e(ult.get("nombre", ult["id"]))}, '
                      f'{fecha_larga(ult["ultima"])}</dd></div>\n')
    partes.append("""</dl>
</section>
<section aria-labelledby="t-lista">
<h2 id="t-lista">Todos los proyectos</h2>
<div class="filtros">
<label for="buscar">Buscar</label>
<input id="buscar" type="search" placeholder="Nombre, tecnología, palabra…" autocomplete="off">
<div class="grupo" role="group" aria-label="Filtrar por estado">
<button type="button" class="filtro" data-estado="" aria-pressed="true">Todos</button>
""")
    for k, nombre in ESTADOS.items():
        if cuenta[k]:
            partes.append(f'<button type="button" class="filtro" data-estado="{k}" aria-pressed="false">{e(nombre)}</button>\n')
    partes.append('</div>\n</div>\n<p id="cuantos" class="nota" role="status" aria-live="polite"></p>\n<div class="tarjetas">\n')
    for p in proyectos:
        tec = "".join(f"<li>{e(t)}</li>" for t in p.get("tecnologias", []))
        texto = " ".join([p.get("nombre", ""), p.get("lema", ""), " ".join(p.get("tecnologias", [])),
                          " ".join(p.get("resumen", [])), p.get("etapa_actual", "")]).lower()
        partes.append(f"""<article class="tarjeta" data-estado="{e(p.get('estado', ''))}" data-texto="{e(texto)}" data-fecha="{e(p['ultima'])}">
<div class="tarjeta-cabeza">
<h3><a href="p/{e(p['id'])}.html">{e(p.get('nombre', p['id']))}</a></h3>
{etiqueta_estado(p)}
</div>
<p class="lema">{e(p.get('lema', ''))}</p>
{barra(p)}
<dl class="datos">
<div><dt>Etapa</dt><dd>{e(p.get('etapa_actual', ''))}</dd></div>
<div><dt>Siguiente paso</dt><dd>{e(p.get('siguiente_paso', ''))}</dd></div>
<div><dt>Último movimiento</dt><dd>{fecha_larga(p['ultima'])} <span class="hace"></span></dd></div>
</dl>
<ul class="tecnologias" aria-label="Tecnologías">{tec}</ul>
</article>
""")
    if not proyectos:
        partes.append("<p>Todavía no hay proyectos.</p>\n")
    partes.append("</div>\n</section>\n</main>\n")
    partes.append(pie(cfg, ""))
    return "".join(partes)


# ---------- pagina de un proyecto ----------

def pagina(p, cfg):
    m = p.get("medidas", {})
    sec = []  # (ancla, titulo, html)

    sec.append(("corto", "En corto", "".join(f"<p>{en_linea(x)}</p>" for x in p.get("resumen", []))))
    if p.get("siguiente_paso"):
        sec.append(("siguiente", "Siguiente paso", f'<p class="destacado">{en_linea(p["siguiente_paso"])}</p>'))
    if p.get("etapas"):
        filas = "".join(
            f'<li class="etapa etapa-{e(x.get("estado", "").replace(" ", "-"))}">'
            f'<span class="etapa-estado">{e(x.get("estado", "").capitalize())}</span>'
            f'<div><strong>{e(x.get("nombre", ""))}</strong><p>{en_linea(x.get("detalle", ""))}</p></div></li>'
            for x in p["etapas"])
        sec.append(("etapas", "Etapas", f'<ol class="etapas">{filas}</ol>'))
    if p.get("pendiente"):
        sec.append(("pendiente", "Qué falta", lista(p["pendiente"])))
    if p.get("hecho"):
        sec.append(("hecho", "Qué hay hecho", lista(p["hecho"])))
    if p.get("retomar", "").strip():
        sec.append(("retomar", "Memoria para retomar", formato(p["retomar"], nivel=3)))
    if p.get("lecciones"):
        sec.append(("lecciones", "Lecciones aprendidas", lista(p["lecciones"])))
    if p.get("diario"):
        dias = "".join(f'<li><time datetime="{e(d.get("fecha", ""))}">{fecha_larga(d.get("fecha", ""))}</time>'
                       f'<p>{en_linea(d.get("texto", ""))}</p></li>'
                       for d in sorted(p["diario"], key=lambda d: d.get("fecha", ""), reverse=True))
        sec.append(("diario", "Diario", f'<ol class="diario">{dias}</ol>'))
    if p.get("relacionados"):
        rel = "".join(f'<li><strong>{e(r.get("nombre", ""))}.</strong> {en_linea(r.get("relacion", ""))}</li>'
                      for r in p["relacionados"])
        sec.append(("relacionados", "Proyectos relacionados", f"<ul>{rel}</ul>"))
    if p.get("texto_para_claude"):
        sec.append(("claude", "Texto para retomarlo con Claude",
                    '<p>Pega este texto al empezar una sesión y Claude se pone al día.</p>'
                    f'<pre id="texto-claude" tabindex="0">{e(p["texto_para_claude"])}</pre>'
                    '<button type="button" class="boton" data-copiar="texto-claude">Copiar el texto</button>'
                    '<span class="nota" role="status" aria-live="polite" id="copiado"></span>'))

    datos = [("Estado", ESTADOS.get(p.get("estado"), p.get("estado", ""))),
             ("Etapa", p.get("etapa_actual", "")),
             ("Empezó", fecha_larga(p.get("inicio", ""))),
             ("Último movimiento", fecha_larga(p["ultima"]))]
    if m.get("lineas"):
        datos.append(("Tamaño", f'{m["lineas"]:,} líneas en {m.get("archivos_de_codigo", 0)} archivos de código'.replace(",", ".")))
    if m.get("cambios_guardados"):
        datos.append(("Cambios guardados en git", str(m["cambios_guardados"])))
    if p.get("tecnologias"):
        datos.append(("Tecnologías", ", ".join(p["tecnologias"])))

    out = [cabeza(f'{p.get("nombre", p["id"])} · {cfg.get("titulo", "Proyectos")}', p.get("lema", ""), "../")]
    out.append(f"""<header class="cabecera cabecera-proyecto">
<div class="ancho">
<p class="miga"><a href="../index.html">← Todos los proyectos</a></p>
<div class="tarjeta-cabeza">
<h1>{e(p.get('nombre', p['id']))}</h1>
{etiqueta_estado(p)}
</div>
<p class="presentacion">{e(p.get('lema', ''))}</p>
</div>
</header>
<main id="contenido" class="ancho proyecto" data-fecha="{e(p['ultima'])}">
<section aria-labelledby="t-ficha" class="ficha">
<h2 id="t-ficha" class="oculto">Ficha</h2>
{barra(p)}
<p class="nota">{e(p.get('avance_nota', ''))}</p>
<dl class="datos datos-ficha">
""")
    out += [f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>\n" for k, v in datos if v]
    out.append(f"</dl>\n{enlaces_codigo(p, cfg)}\n</section>\n")
    out.append('<nav class="indice" aria-label="Apartados de esta página"><ul>'
               + "".join(f'<li><a href="#{a}">{e(t)}</a></li>' for a, t, _ in sec) + "</ul></nav>\n")
    for a, t, cuerpo in sec:
        out.append(f'<section id="{a}" aria-labelledby="t-{a}">\n<h2 id="t-{a}">{e(t)}</h2>\n{cuerpo}\n</section>\n')
    out.append("</main>\n")
    out.append(pie(cfg, "../"))
    return "".join(out)


# ---------- ordenes ----------

PLANTILLA = {
    "nombre": "", "lema": "", "estado": "activo", "inicio": "", "ultima_actividad": "",
    "avance": 0, "avance_nota": "", "etapa_actual": "", "tecnologias": [],
    "repositorio": "", "codigo_privado": True, "resumen": [""], "siguiente_paso": "",
    "etapas": [{"nombre": "", "estado": "en curso", "detalle": ""}],
    "hecho": [], "pendiente": [], "diario": [{"fecha": "", "texto": ""}],
    "lecciones": [], "relacionados": [], "texto_para_claude": "",
}


def nuevo(ident):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", ident):
        sys.exit("El identificador solo puede llevar minúsculas, números y guiones.")
    carpeta = FICHAS / ident
    if carpeta.exists():
        sys.exit(f"Ya existe {carpeta}")
    carpeta.mkdir(parents=True)
    f = dict(PLANTILLA, nombre=ident, repositorio=ident, inicio=date.today().isoformat(),
             ultima_actividad=date.today().isoformat())
    (carpeta / "ficha.json").write_text(json.dumps(f, ensure_ascii=False, indent=1), encoding="utf-8")
    (carpeta / "retomar.md").write_text(
        "## Qué es y qué se busca\n\n## Cómo ponerlo en marcha\n\n## Cómo está hecho\n\n"
        "## Dónde está ahora\n\n## Qué falta\n", encoding="utf-8")
    print(f"Creada la ficha en {carpeta}. Rellénala y ejecuta: python generar.py")


def generar():
    cfg = leer_json(RAIZ / "config.json")
    proyectos = cargar()
    SALIDA.mkdir(exist_ok=True)
    vivos = set()
    for p in proyectos:
        (SALIDA / f"{p['id']}.html").write_text(pagina(p, cfg), encoding="utf-8")
        vivos.add(f"{p['id']}.html")
    for viejo in SALIDA.glob("*.html"):
        if viejo.name not in vivos:
            viejo.unlink()
    (RAIZ / "index.html").write_text(portada(proyectos, cfg), encoding="utf-8")
    (RAIZ / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Web generada: {len(proyectos)} proyecto(s).")
    if not cfg.get("usuario_github"):
        print("OJO: falta usuario_github en config.json; no salen los botones de ver y descargar el código.")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "nuevo":
        nuevo(sys.argv[2])
    else:
        generar()
