"""Genera la web de proyectos (un portfolio) a partir de las fichas.

    python generar.py              rehace la web entera
    python generar.py nuevo ID     crea la ficha vacia de un proyecto nuevo (ID sin espacios)

Cada proyecto es una carpeta en fichas\\ID con:
    ficha.json    los datos y las listas (estado, etapas, hecho, pendiente, diario, lecciones)
                  y, si se quiere, "color" y "esquema" (el dibujo de la estructura del programa)
    retomar.md    la memoria larga para ponerse al dia
    portada.svg   la imagen del proyecto (tambien vale .jpg, .png o .webp). Si falta, se dibuja una
    medidas.json  lo escribe este programa si en local.json consta donde esta el codigo

Solo usa lo que trae Python."""
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
FICHAS = RAIZ / "fichas"
SALIDA = RAIZ / "p"
PORTADAS = SALIDA / "portadas"

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
IMAGENES = (".svg", ".webp", ".jpg", ".jpeg", ".png")
COLOR = "#5eead4"
FUENTES = ("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600"
           "&family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@500;700&display=swap")


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


def miles(n):
    return f"{int(n):,}".replace(",", ".")


def color_de(p):
    c = str(p.get("color", ""))
    return c if re.fullmatch(r"#[0-9a-fA-F]{6}", c) else COLOR


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
        p["_carpeta"] = carpeta
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


# ---------- la imagen de cada proyecto ----------

def portada_dibujada(p):
    """Una portada sobria para el proyecto que no trae la suya."""
    c = color_de(p)
    n = int(hashlib.md5(p["id"].encode("utf-8")).hexdigest(), 16)
    aros = "".join(
        f'<circle cx="{820 + (n >> (i * 3)) % 140}" cy="{300 + (n >> (i * 5)) % 120}" r="{90 + i * 78}" '
        f'fill="none" stroke="{c}" stroke-opacity="{0.34 - i * 0.05:.2f}" stroke-width="1.5"/>'
        for i in range(6))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675">
<defs><linearGradient id="f" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1220"/><stop offset="1" stop-color="#121a2b"/></linearGradient>
<radialGradient id="l" cx="72%" cy="48%" r="55%"><stop offset="0" stop-color="{c}" stop-opacity=".30"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient></defs>
<rect width="1200" height="675" fill="url(#f)"/><rect width="1200" height="675" fill="url(#l)"/>
{aros}
<text x="80" y="560" font-family="ui-monospace,Consolas,monospace" font-size="34" fill="{c}">&gt; {e(p['id'])}_</text>
</svg>
"""


def preparar_portada(p):
    """Deja la imagen en p\\portadas y devuelve su nombre de archivo."""
    PORTADAS.mkdir(parents=True, exist_ok=True)
    for ext in IMAGENES:
        origen = p["_carpeta"] / f"portada{ext}"
        if origen.is_file():
            nombre = f"{p['id']}{ext}"
            shutil.copyfile(origen, PORTADAS / nombre)
            return nombre
    nombre = f"{p['id']}.svg"
    (PORTADAS / nombre).write_text(portada_dibujada(p), encoding="utf-8")
    return nombre


# ---------- el esquema de la estructura ----------

def esquema(esq, ident):
    """Dibuja grupos de elementos en columnas y las conexiones entre ellos.

    "grupos": [{"nombre", "columna" (opcional), "elementos": [{"id", "nombre", "detalle", "destacado"}]}]
    "conexiones": [{"de", "a", "texto", "fuerte", "doble"}]"""
    grupos = [g for g in esq.get("grupos", []) if g.get("elementos")]
    if not grupos:
        return ""
    columnas, sig = {}, 0
    for g in grupos:
        c = g.get("columna")
        if isinstance(c, int):
            sig = max(sig, c)
        else:
            sig += 1
            c = sig
        columnas.setdefault(c, []).append(g)
    orden = sorted(columnas)
    NW, NH, NG, GP, GH, GG, CG, M = 204, 56, 12, 14, 36, 22, 92, 18
    GW = NW + 2 * GP

    def alto(g):
        n = len(g["elementos"])
        return GH + n * NH + (n - 1) * NG + GP

    altos = {c: sum(alto(g) for g in columnas[c]) + GG * (len(columnas[c]) - 1) for c in orden}
    H = max(altos.values()) + 2 * M
    W = 2 * M + len(orden) * GW + (len(orden) - 1) * CG
    pos, nombres, cajas, nodos = {}, {}, [], []
    for i, c in enumerate(orden):
        x = M + i * (GW + CG)
        y = M + (H - 2 * M - altos[c]) / 2
        for g in columnas[c]:
            h = alto(g)
            cajas.append(f'<g class="esq-grupo"><rect x="{x}" y="{y:.0f}" width="{GW}" height="{h}" rx="16"/>'
                         f'<text x="{x + GP + 2}" y="{y + 23:.0f}">{e(g.get("nombre", ""))}</text></g>')
            ny = y + GH
            for el in g["elementos"]:
                pos[el.get("id")] = (x + GP, ny, i)
                nombres[el.get("id")] = el.get("nombre", "")
                clase = "esq-nodo destacado" if el.get("destacado") else "esq-nodo"
                nodos.append(
                    f'<g class="{clase}"><rect x="{x + GP}" y="{ny:.0f}" width="{NW}" height="{NH}" rx="11"/>'
                    f'<text class="esq-nombre" x="{x + GP + 14}" y="{ny + 24:.0f}">{e(el.get("nombre", ""))}</text>'
                    f'<text class="esq-detalle" x="{x + GP + 14}" y="{ny + 42:.0f}">{e(el.get("detalle", ""))}</text></g>')
                ny += NH + NG
            y += h + GG
    lineas, rotulos = [], []
    for con in esq.get("conexiones", []):
        a, b = pos.get(con.get("de")), pos.get(con.get("a"))
        if not a or not b:
            print(f"OJO: el esquema de {ident} nombra un elemento que no existe: {con}")
            continue
        (ax, ay, ac), (bx, by, bc) = a, b
        ay, by = ay + NH / 2, by + NH / 2
        if ac == bc:
            if abs(by - ay) <= NH + GG + GH + GP + 1:      # vecinos: una linea recta
                cx = ax + NW / 2
                y1, y2 = (ay + NH / 2, by - NH / 2) if by > ay else (ay - NH / 2, by + NH / 2)
                d = f"M{cx:.0f} {y1:.0f} L{cx:.0f} {y2:.0f}"
                rx, ry = cx + 10, (y1 + y2) / 2 + 4
                ancla = "start"
            else:                                           # lejanos: un arco por la derecha
                x1 = ax + NW
                d = f"M{x1} {ay:.0f} C{x1 + 46} {ay:.0f} {x1 + 46} {by:.0f} {x1} {by:.0f}"
                rx, ry, ancla = x1 + 40, (ay + by) / 2 + 4, "start"
        else:
            x1, x2 = (ax + NW, bx) if bc > ac else (ax, bx + NW)
            m = (x2 - x1) / 2
            d = f"M{x1} {ay:.0f} C{x1 + m:.0f} {ay:.0f} {x2 - m:.0f} {by:.0f} {x2} {by:.0f}"
            rx, ry, ancla = (x1 + x2) / 2, (ay + by) / 2 - 7, "middle"
        fuerte = " fuerte" if con.get("fuerte") else ""
        punta = f"punta-{ident}{'-f' if fuerte else ''}"
        inicio = f' marker-start="url(#{punta})"' if con.get("doble") else ""
        lineas.append(f'<path class="esq-linea{fuerte}" d="{d}" marker-end="url(#{punta})"{inicio}/>')
        if con.get("texto"):
            rotulos.append(f'<text class="esq-rotulo{fuerte}" x="{rx:.0f}" y="{ry:.0f}" '
                           f'text-anchor="{ancla}">{e(con["texto"])}</text>')

    def punta(sufijo, clase):
        return (f'<marker id="punta-{ident}{sufijo}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                f'markerHeight="7" orient="auto-start-reverse"><path class="{clase}" d="M0 1 L10 5 L0 9 z"/></marker>')

    dibujo = (f'<svg class="esq" viewBox="0 0 {W} {H:.0f}" style="min-width:{W * 0.62:.0f}px" role="img" '
              f'aria-label="{e(esq.get("titulo", "Esquema de la estructura del programa"))}. '
              f'Debajo está el mismo esquema en texto.">'
              f'<defs>{punta("", "esq-punta")}{punta("-f", "esq-punta fuerte")}</defs>'
              + "".join(cajas) + "".join(lineas) + "".join(nodos) + "".join(rotulos) + "</svg>")

    partes = "".join(
        f'<li><strong>{e(g.get("nombre", ""))}.</strong> '
        + "; ".join(f'{e(el.get("nombre", ""))}{": " + e(el["detalle"]) if el.get("detalle") else ""}'
                    for el in g["elementos"]) + ".</li>"
        for g in grupos)
    flechas = "".join(
        f'<li>{e(nombres[c["de"]])} {"↔" if c.get("doble") else "→"} {e(nombres[c["a"]])}'
        f'{": " + e(c["texto"]) if c.get("texto") else ""}</li>'
        for c in esq.get("conexiones", []) if c.get("de") in nombres and c.get("a") in nombres)
    intro = f'<p>{en_linea(esq["texto"])}</p>' if esq.get("texto") else ""
    return (f'{intro}<div class="esq-marco" tabindex="0" role="group" aria-label="Esquema. Se puede desplazar a los lados.">'
            f'{dibujo}</div>'
            f'<details class="plegable"><summary>Leer el esquema como texto</summary>'
            f'<h3>Elementos</h3><ul>{partes}</ul><h3>Conexiones</h3><ul>{flechas}</ul></details>')


# ---------- piezas de pagina ----------

def cabeza(titulo, descripcion, raiz, cfg, color=COLOR):
    autor = cfg.get("autor") or cfg.get("usuario_github") or "Portfolio"
    usuario = cfg.get("usuario_github", "")
    gh = (f'<a class="barra-gh" href="https://github.com/{e(usuario)}">GitHub</a>' if usuario else "")
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descripcion)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FUENTES}">
<link rel="stylesheet" href="{raiz}estilo.css">
</head>
<body style="--color:{color}">
<a class="saltar" href="#contenido">Saltar al contenido</a>
<header class="barra">
<div class="ancho barra-dentro">
<a class="marca" href="{raiz}index.html">{e(autor)}<span aria-hidden="true">_</span></a>
<nav aria-label="Principal">
<a href="{raiz}index.html#proyectos">Proyectos</a>
<a href="{raiz}index.html#oficio">Cómo trabajo</a>
<a href="{raiz}index.html#tecnologias">Tecnologías</a>
{gh}
</nav>
</div>
</header>
"""


def pie(cfg, raiz):
    autor = cfg.get("autor") or cfg.get("usuario_github") or ""
    return f"""<footer class="pie">
<div class="ancho">
<p>{e(autor)} · {e(cfg.get('titulo', 'Proyectos'))}. Página actualizada el {fecha_larga(date.today().isoformat())}.</p>
</div>
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


def lista(elementos, clase=""):
    cl = f' class="{clase}"' if clase else ""
    return f"<ul{cl}>" + "".join(f"<li>{en_linea(x)}</li>" for x in elementos) + "</ul>"


# ---------- portada ----------

def portada(proyectos, cfg):
    cuenta = {k: sum(1 for p in proyectos if p.get("estado") == k) for k in ESTADOS}
    autor = cfg.get("autor") or cfg.get("usuario_github") or ""
    usuario = cfg.get("usuario_github", "")
    lineas = sum(int(p["medidas"].get("lineas", 0) or 0) for p in proyectos)
    tec = {}
    for p in proyectos:
        for t in p.get("tecnologias", []):
            tec.setdefault(t, []).append(p.get("nombre", p["id"]))
    titulo_web = f'{autor} · {cfg.get("titulo", "Proyectos")}' if autor else cfg.get("titulo", "Proyectos")
    partes = [cabeza(titulo_web, cfg.get("presentacion", ""), "", cfg)]
    gh = (f'<a class="boton boton-claro" href="https://github.com/{e(usuario)}">Perfil de GitHub</a>'
          if usuario else "")
    partes.append(f"""<main id="contenido">
<section class="heroe" aria-labelledby="t-heroe">
<div class="ancho">
<p class="antetitulo">{e(cfg.get('antetitulo', 'Portfolio'))}</p>
<h1 id="t-heroe">{e(cfg.get('titular') or cfg.get('titulo', 'Proyectos'))}</h1>
<p class="presentacion">{e(cfg.get('presentacion', ''))}</p>
<div class="botones"><a class="boton" href="#proyectos">Ver los proyectos</a>{gh}</div>
<dl class="cifras">
<div><dt>Proyectos</dt><dd>{len(proyectos)}</dd></div>
""")
    if lineas:
        partes.append(f"<div><dt>Líneas de código</dt><dd>{miles(lineas)}</dd></div>\n")
    if tec:
        partes.append(f"<div><dt>Tecnologías</dt><dd>{len(tec)}</dd></div>\n")
    if proyectos:
        ult = max(proyectos, key=lambda p: p["ultima"])
        partes.append(f'<div class="cifra-larga"><dt>Último movimiento</dt><dd>{e(ult.get("nombre", ult["id"]))}, '
                      f'{fecha_larga(ult["ultima"])}</dd></div>\n')
    partes.append("""</dl>
</div>
</section>
<section id="proyectos" class="ancho" aria-labelledby="t-lista">
<p class="antetitulo">Trabajo</p>
<h2 id="t-lista">Proyectos</h2>
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
        etiquetas = "".join(f"<li>{e(t)}</li>" for t in p.get("tecnologias", []))
        texto = " ".join([p.get("nombre", ""), p.get("lema", ""), " ".join(p.get("tecnologias", [])),
                          " ".join(p.get("resumen", [])), p.get("etapa_actual", "")]).lower()
        tam = (f'<div><dt>Tamaño</dt><dd>{miles(p["medidas"]["lineas"])} líneas</dd></div>'
               if p["medidas"].get("lineas") else "")
        partes.append(f"""<article class="tarjeta" style="--color:{color_de(p)}" data-estado="{e(p.get('estado', ''))}" data-texto="{e(texto)}" data-fecha="{e(p['ultima'])}">
<a class="tarjeta-foto" href="p/{e(p['id'])}.html" tabindex="-1" aria-hidden="true"><img src="p/portadas/{e(p['_portada'])}" alt="" loading="lazy" width="1200" height="675"></a>
<div class="tarjeta-cuerpo">
<div class="tarjeta-cabeza">
<h3><a href="p/{e(p['id'])}.html">{e(p.get('nombre', p['id']))}</a></h3>
{etiqueta_estado(p)}
</div>
<p class="lema">{e(p.get('lema', ''))}</p>
{barra(p)}
<dl class="datos">
<div><dt>Etapa</dt><dd>{e(p.get('etapa_actual', ''))}</dd></div>
<div><dt>Siguiente paso</dt><dd>{e(p.get('siguiente_paso', ''))}</dd></div>
{tam}
<div><dt>Último movimiento</dt><dd>{fecha_larga(p['ultima'])} <span class="hace"></span></dd></div>
</dl>
<ul class="tecnologias" aria-label="Tecnologías">{etiquetas}</ul>
<p class="tarjeta-mas"><a href="p/{e(p['id'])}.html">Ver el proyecto y su esquema<span class="oculto">: {e(p.get('nombre', p['id']))}</span> →</a></p>
</div>
</article>
""")
    if not proyectos:
        partes.append("<p>Todavía no hay proyectos.</p>\n")
    partes.append("</div>\n</section>\n")

    if cfg.get("principios") or cfg.get("sobre_mi"):
        partes.append('<section id="oficio" class="ancho" aria-labelledby="t-oficio">\n'
                      '<p class="antetitulo">Oficio</p>\n<h2 id="t-oficio">Cómo trabajo</h2>\n')
        partes.append('<div class="sobre">' + "".join(f"<p>{en_linea(x)}</p>" for x in cfg.get("sobre_mi", [])) + "</div>\n")
        if cfg.get("principios"):
            partes.append('<ol class="principios">' + "".join(
                f'<li><h3>{e(x.get("titulo", ""))}</h3><p>{en_linea(x.get("texto", ""))}</p></li>'
                for x in cfg["principios"]) + "</ol>\n")
        partes.append("</section>\n")

    if tec:
        filas = "".join(
            f'<li><span class="tec-nombre">{e(t)}</span><span class="tec-donde">{e(", ".join(donde))}</span></li>'
            for t, donde in sorted(tec.items(), key=lambda x: (-len(x[1]), x[0].lower())))
        partes.append('<section id="tecnologias" class="ancho" aria-labelledby="t-tec">\n'
                      '<p class="antetitulo">Herramientas</p>\n<h2 id="t-tec">Tecnologías</h2>\n'
                      '<p class="nota">Cada una, con los proyectos donde está usada de verdad.</p>\n'
                      f'<ul class="tec-lista">{filas}</ul>\n</section>\n')

    if usuario:
        partes.append(f"""<section id="contacto" class="ancho" aria-labelledby="t-contacto">
<div class="llamada">
<h2 id="t-contacto">{e(cfg.get('contacto_titulo', '¿Hablamos?'))}</h2>
<p>{e(cfg.get('contacto_texto', 'El código y el día a día de los proyectos están en GitHub.'))}</p>
<a class="boton" href="https://github.com/{e(usuario)}">github.com/{e(usuario)}</a>
</div>
</section>
""")
    partes.append("</main>\n")
    partes.append(pie(cfg, ""))
    return "".join(partes)


# ---------- pagina de un proyecto ----------

def pagina(p, cfg):
    m = p.get("medidas", {})
    sec = []  # (ancla, titulo, html, clase)

    sec.append(("corto", "En corto", "".join(f"<p>{en_linea(x)}</p>" for x in p.get("resumen", [])), "texto"))
    if p.get("esquema"):
        dibujo = esquema(p["esquema"], re.sub(r"[^a-z0-9]", "", p["id"]))
        if dibujo:
            sec.append(("esquema", "Cómo está hecho", dibujo, ""))
    if p.get("siguiente_paso"):
        sec.append(("siguiente", "Siguiente paso", f'<p class="destacado">{en_linea(p["siguiente_paso"])}</p>', "texto"))
    if p.get("etapas"):
        filas = "".join(
            f'<li class="etapa etapa-{e(x.get("estado", "").replace(" ", "-"))}">'
            f'<span class="etapa-estado">{e(x.get("estado", "").capitalize())}</span>'
            f'<div><strong>{e(x.get("nombre", ""))}</strong><p>{en_linea(x.get("detalle", ""))}</p></div></li>'
            for x in p["etapas"])
        sec.append(("etapas", "Etapas", f'<ol class="etapas">{filas}</ol>', ""))
    if p.get("hecho"):
        sec.append(("hecho", "Qué hay hecho", lista(p["hecho"], "marcas hechas"), ""))
    if p.get("pendiente"):
        sec.append(("pendiente", "Qué falta", lista(p["pendiente"], "marcas faltan"), ""))
    if p.get("lecciones"):
        sec.append(("lecciones", "Lecciones aprendidas", lista(p["lecciones"], "lecciones"), ""))
    if p.get("diario"):
        dias = "".join(f'<li><time datetime="{e(d.get("fecha", ""))}">{fecha_larga(d.get("fecha", ""))}</time>'
                       f'<p>{en_linea(d.get("texto", ""))}</p></li>'
                       for d in sorted(p["diario"], key=lambda d: d.get("fecha", ""), reverse=True))
        sec.append(("diario", "Diario", f'<ol class="diario">{dias}</ol>', ""))
    if p.get("retomar", "").strip():
        sec.append(("retomar", "Memoria para retomar",
                    '<p class="nota">El cuaderno técnico del proyecto: lo necesario para ponerse al día y seguir.</p>'
                    '<details class="plegable cuaderno"><summary>Abrir la memoria para retomar</summary>'
                    f'{formato(p["retomar"], nivel=3)}</details>', "texto"))
    if p.get("relacionados"):
        rel = "".join(f'<li><strong>{e(r.get("nombre", ""))}.</strong> {en_linea(r.get("relacion", ""))}</li>'
                      for r in p["relacionados"])
        sec.append(("relacionados", "Proyectos relacionados", f"<ul>{rel}</ul>", "texto"))
    if p.get("texto_para_claude"):
        sec.append(("claude", "Texto para retomarlo con Claude",
                    '<p>Pega este texto al empezar una sesión y Claude se pone al día.</p>'
                    f'<pre id="texto-claude" tabindex="0">{e(p["texto_para_claude"])}</pre>'
                    '<button type="button" class="boton" data-copiar="texto-claude">Copiar el texto</button>'
                    '<span class="nota" role="status" aria-live="polite" id="copiado"></span>', "texto"))

    datos = [("Etapa", p.get("etapa_actual", "")),
             ("Empezó", fecha_larga(p.get("inicio", ""))),
             ("Último movimiento", fecha_larga(p["ultima"]))]
    if m.get("lineas"):
        datos.append(("Tamaño", f'{miles(m["lineas"])} líneas en {m.get("archivos_de_codigo", 0)} archivos de código'))
    if m.get("cambios_guardados"):
        datos.append(("Cambios guardados en git", str(m["cambios_guardados"])))

    etiquetas = "".join(f"<li>{e(t)}</li>" for t in p.get("tecnologias", []))
    out = [cabeza(f'{p.get("nombre", p["id"])} · {cfg.get("titulo", "Proyectos")}', p.get("lema", ""), "../",
                  cfg, color_de(p))]
    out.append(f"""<main id="contenido" class="proyecto" data-fecha="{e(p['ultima'])}">
<section class="heroe heroe-proyecto" aria-labelledby="t-proyecto">
<div class="ancho heroe-dos">
<div>
<p class="miga"><a href="../index.html#proyectos">← Todos los proyectos</a></p>
<div class="tarjeta-cabeza">
<h1 id="t-proyecto">{e(p.get('nombre', p['id']))}</h1>
{etiqueta_estado(p)}
</div>
<p class="presentacion">{e(p.get('lema', ''))}</p>
{barra(p)}
<p class="nota">{e(p.get('avance_nota', ''))}</p>
<ul class="tecnologias" aria-label="Tecnologías">{etiquetas}</ul>
{enlaces_codigo(p, cfg)}
</div>
<figure class="foto"><img src="portadas/{e(p['_portada'])}" alt="Ilustración del proyecto {e(p.get('nombre', p['id']))}" width="1200" height="675"></figure>
</div>
</section>
<div class="ancho">
<dl class="datos datos-ficha">
""")
    out += [f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>\n" for k, v in datos if v]
    out.append("</dl>\n")
    out.append('<nav class="indice" aria-label="Apartados de esta página"><ul>'
               + "".join(f'<li><a href="#{a}">{e(t)}</a></li>' for a, t, _, _ in sec) + "</ul></nav>\n")
    for a, t, cuerpo, clase in sec:
        cl = f' class="{clase}"' if clase else ""
        out.append(f'<section id="{a}" aria-labelledby="t-{a}"{cl}>\n<h2 id="t-{a}">{e(t)}</h2>\n{cuerpo}\n</section>\n')
    out.append("</div>\n</main>\n")
    out.append(pie(cfg, "../"))
    return "".join(out)


# ---------- ordenes ----------

PLANTILLA = {
    "nombre": "", "lema": "", "estado": "activo", "inicio": "", "ultima_actividad": "",
    "avance": 0, "avance_nota": "", "etapa_actual": "", "tecnologias": [], "color": COLOR,
    "repositorio": "", "codigo_privado": True, "resumen": [""], "siguiente_paso": "",
    "etapas": [{"nombre": "", "estado": "en curso", "detalle": ""}],
    "hecho": [], "pendiente": [], "diario": [{"fecha": "", "texto": ""}],
    "lecciones": [], "relacionados": [], "texto_para_claude": "",
    "esquema": {"titulo": "", "texto": "", "grupos": [], "conexiones": []},
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
    fotos = set()
    for p in proyectos:
        p["_portada"] = preparar_portada(p)
        fotos.add(p["_portada"])
    vivos = set()
    for p in proyectos:
        (SALIDA / f"{p['id']}.html").write_text(pagina(p, cfg), encoding="utf-8")
        vivos.add(f"{p['id']}.html")
    for viejo in SALIDA.glob("*.html"):
        if viejo.name not in vivos:
            viejo.unlink()
    for vieja in PORTADAS.glob("*") if PORTADAS.is_dir() else []:
        if vieja.name not in fotos:
            vieja.unlink()
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
