#!/usr/bin/env python3
"""One-off generator: reference/ (Webflow export) -> site/ (clean static site).
Not part of the deliverable. Re-runnable."""
import re, os, json, html, shutil, subprocess, hashlib, urllib.parse
from html.parser import HTMLParser

import sys
sys.path.insert(0, os.environ["SCRATCH"])
from alt_text import ALT
from alt_ja import JA
from meta_text import META

PROJ = "/Users/konomi/Documents/portfolio-site"
REF = PROJ + "/reference"
SITE = PROJ + "/site"
MAN = json.load(open(REF + "/manifest.json"))
CDN = "https://cdn.prod.website-files.com/65b3f97bc0a7ba11f49c439c/"
ZWJ = "‍"

# ------------------------------------------------------------------ DOM
VOID = {"img", "br", "meta", "link", "input", "hr"}


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    @property
    def cls(self):
        return set(self.attrs.get("class", "").split())

    def find_all(self, pred):
        out = []
        for c in self.children:
            if isinstance(c, Node):
                if pred(c):
                    out.append(c)
                out += c.find_all(pred)
        return out


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root", {})
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def parse(path):
    p = Parser()
    p.feed(open(path).read())
    return p.root


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def attr_esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;")


# ------------------------------------------------------------------ images
IMG_ORDER = ["goodwill", "honda", "robot", "medium", "about", "index", "projects", "ai-process"]
img_by_md5 = {}   # md5 -> site-relative path
img_dims = {}     # site-relative path -> (w,h)
used = {}         # (slug, clean name) -> md5


RENAME = {"000008290007": "schwangau-bavaria", "000008290026_original-1": "kumano-wakayama",
          "8": "kuroshima-okinawa", "000222350009": "kawagoe-saitama"}


def clean_name(fname):
    fname = urllib.parse.unquote(fname)
    fname = re.sub(r"^[0-9a-f]{24}_", "", fname)
    fname = re.sub(r"^[0-9a-f]{32}_", "", fname)
    stem, ext = os.path.splitext(fname)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-").lower()
    stem = re.sub(r"-{2,}", "-", stem)
    m = re.fullmatch(r"(.*?)(-p-\d+)?", stem)
    base, variant = m.group(1), m.group(2) or ""
    base = RENAME.get(base, base)
    return base + variant + ext.lower()


def local_asset(url):
    dest = MAN["assets"].get(url) or MAN["assets"].get(urllib.parse.quote(urllib.parse.unquote(url), safe=":/()"))
    if not dest:
        raise KeyError(url)
    return REF + "/" + dest


def place_image(url, slug):
    """Copy one asset into site/images/<slug>/ (deduped by content). Returns /images/... path."""
    src = local_asset(url)
    data = open(src, "rb").read()
    md5 = hashlib.md5(data).hexdigest()
    if md5 in img_by_md5:
        return img_by_md5[md5]
    name = clean_name(os.path.basename(src))
    rel = f"images/{slug}/{name}"
    assert (slug, name) not in used or used[(slug, name)] == md5, f"name clash {rel}"
    used[(slug, name)] = md5
    dst = f"{SITE}/{rel}"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "wb").write(data)
    img_by_md5[md5] = "/" + rel
    return "/" + rel


def dims(web_path):
    if web_path in img_dims:
        return img_dims[web_path]
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", SITE + web_path],
                         capture_output=True, text=True).stdout
    w = int(re.search(r"pixelWidth: (\d+)", out).group(1))
    h = int(re.search(r"pixelHeight: (\d+)", out).group(1))
    img_dims[web_path] = (w, h)
    return w, h


def img_tag(n, slug, cls=None, width=None, loading="lazy", sizes=None):
    a = n.attrs
    src = a["src"]
    main = place_image(src, slug)
    w, h = dims(main)
    parts = [f'class="{cls}"'] if cls else []
    parts.append(f'src="{main}"')
    if a.get("srcset"):
        entries = []
        for e in a["srcset"].split(","):
            u, d = e.strip().rsplit(" ", 1)
            entries.append(f"{place_image(u, slug)} {d}")
        parts.append('srcset="' + ", ".join(entries) + '"')
        sz = sizes or a.get("sizes")
        if sz:
            parts.append(f'sizes="{sz}"')
    if width:
        parts += [f'width="{width}"', f'height="{round(width * h / w)}"']
    else:
        parts += [f'width="{w}"', f'height="{h}"']
    en = ALT[main][0]
    alt = "&#10;".join(["AI-generated alt text", "English: " + attr_esc(en), "日本語：" + attr_esc(JA[main])])
    parts.append(f'alt="{alt}"')
    if loading:
        parts.append(f'loading="{loading}"')
    if loading == "eager":
        parts.append('fetchpriority="high"')
    return "<img " + " ".join(parts) + ">"


# ------------------------------------------------------------------ inline conversion
CSS_CUSTOM = open(os.environ["SCRATCH"] + "/custom.css").read()
DECL = {}
for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", CSS_CUSTOM.split("@media")[0]):
    for sel in m.group(1).split(","):
        sel = sel.strip()
        if sel.startswith(".") and re.fullmatch(r"\.[\w-]+", sel):
            DECL.setdefault(sel[1:], "")
            DECL[sel[1:]] += m.group(2)


def span_kind(classes):
    d = "".join(DECL.get(c, "") for c in classes)
    if "#dbc4a5" in d:
        return "heavy" if re.search(r"font-weight:\s*900", d) else "mark"
    if "#b80707" in d:
        return "asterisk"
    if re.search(r"font-weight:\s*(600|700|800|900)", d):
        return "strong"
    return None


SPECIAL_SPAN = {"text-span-27": "note__label", "text-span-32": "latin"}


def href_map(h):
    if h.startswith("/") and not h.startswith("//") and h != "/" and not h.endswith("/"):
        return h + "/"
    return h


def inline(children):
    s = ""
    for c in children:
        if isinstance(c, str):
            s += esc(c)
            continue
        t, k = c.tag, c.cls
        if t == "br":
            s += "<br>"
        elif t == "sup":
            s += "<sup>" + inline(c.children) + "</sup>"
        elif t in ("em", "i"):
            inner = inline(c.children)
            if inner.strip(ZWJ + " "):
                s += "<em>" + inner + "</em>"
            else:
                s += inner
        elif t in ("strong", "b"):
            kind = span_kind(k)
            inner = inline(c.children)
            if not inner.strip(ZWJ + " "):
                s += inner
            elif kind in ("mark", "heavy"):
                s += ('<mark class="heavy">' if kind == "heavy" else "<mark>") + inner + "</mark>"
            else:
                s += "<strong>" + inner + "</strong>"
        elif t == "a":
            s += f'<a href="{attr_esc(href_map(c.attrs.get("href", "")))}">' + inline(c.children) + "</a>"
        elif t == "span":
            special = next((SPECIAL_SPAN[x] for x in k if x in SPECIAL_SPAN), None)
            kind = span_kind(k)
            inner = inline(c.children)
            if special:
                s += f'<span class="{special}">{inner}</span>'
            elif kind == "mark":
                s += f"<mark>{inner}</mark>"
            elif kind == "heavy":
                s += f'<mark class="heavy">{inner}</mark>'
            elif kind == "asterisk":
                s += f'<span class="asterisk">{inner}</span>'
            elif kind == "strong":
                s += f"<strong>{inner}</strong>"
            elif re.search(r"font-weight:\s*400", "".join(DECL.get(x, "") for x in k)):
                s += f"<span>{inner}</span>"
            else:
                s += inner
        else:
            s += inline(c.children)
    return s


def hoist_breaks(h):
    """Move <br>/ZWJ runs out of the edges of inline tags so paragraphs can be split safely."""
    run = r"(?:<br>|" + ZWJ + r")+"
    prev = None
    while prev != h:
        prev = h
        h = re.sub(r"(" + run + r")(</(?:strong|em|mark|span)>)", r"\2\1", h)
        h = re.sub(r"(<(?:strong|em|mark|span)(?: [^>]*)?>)(" + run + r")", r"\2\1", h)
    return h


def paragraphs(inner_html):
    """Turn Webflow's <br>[ZWJ]<br> 'paragraphs' into real <p> elements.
    k consecutive <br> = k-1 blank lines; one blank line = normal paragraph gap."""
    inner_html = hoist_breaks(inner_html)
    sep = re.compile(r"((?:<br>[\s" + ZWJ + r"]*)+)")
    parts = sep.split(inner_html)
    paras, cur = [], parts[0]
    gaps = []
    i = 1
    while i < len(parts):
        brs, text = parts[i], parts[i + 1]
        k = brs.count("<br>")
        if k == 1:
            cur += "<br>" + text
        else:
            paras.append(cur)
            gaps.append(k - 1)
            cur = text
        i += 2
    paras.append(cur)
    # trailing run of <br>s (e.g. "…。<br><br>") leaves blank lines after the last paragraph
    trail = 0
    if parts[-1].replace(ZWJ, "").strip() == "" and len(parts) > 1:
        tail = parts[-2]
        k_tail = tail.count("<br>")
        zwj_last = ZWJ in tail.rsplit("<br>", 1)[-1]
        trail = max(0, k_tail - 1) + (1 if zwj_last else 0)
    out = []
    for idx, p in enumerate(paras):
        p = p.replace(ZWJ, "").strip()
        if not p:
            # blank leading/trailing paragraph (trailing <br>) – fold gap into previous
            continue
        g = gaps[idx] if idx < len(gaps) else 1
        c = ""
        out.append(f"<p{c}>{p}</p>")
    return "\n".join(out)


# ------------------------------------------------------------------ article conversion
def is_container(n):
    return isinstance(n, Node) and n.tag == "div" and "w-container" in n.cls


def text_of(n):
    return "".join(c if isinstance(c, str) else text_of(c) for c in n.children)


NOTE_CLASS = {
    "text-block-29": "note",
    "text-block-30": "note",
    "text-block-31": "note",
    "text-block-33": "note",
    "text-block-32": "note note--quote",
}


class Article:
    def __init__(self, slug):
        self.slug = slug
        self.out = []
        self.seen_h2 = False

    def emit(self, s, ind=3):
        self.out.append("  " * ind + s.replace("\n", "\n" + "  " * ind))

    def children(self, node):
        for c in node.children:
            if isinstance(c, str):
                continue
            self.node(c)

    def node(self, n):
        k, t = n.cls, n.tag
        if t == "img":
            self.emit(img_tag(n, self.slug, "shot"))
        elif t == "h1" and "h1" in k:
            self.emit(f'<h1 class="article-title">{inline(n.children)}</h1>')
        elif "h2" in k:
            self.emit(f'<p class="article-subtitle">{inline(n.children)}</p>')
        elif "h3" in k:
            self.seen_h2 = True
            self.emit(f'<h2 class="section-title">{inline(n.children)}</h2>')
        elif "text-block-5" in k:
            self.emit(f'<p class="meta">{inline(n.children)}</p>')
        elif "body-article" in k:
            self.emit('<div class="prose">\n  ' + paragraphs(inline(n.children)).replace("\n", "\n  ") + "\n</div>")
        elif any(c in NOTE_CLASS for c in k):
            cls = next(NOTE_CLASS[c] for c in k if c in NOTE_CLASS)
            # the original reused its "quote" style for one footnote on Honda; only real quotes keep the bar
            if "quote" in cls and text_of(n).lstrip(ZWJ + " \n").startswith("*"):
                cls = "note"
            self.emit(f'<p class="{cls}">{inline(n.children).replace(ZWJ, "")}</p>')
        elif t == "ul":
            numbered = "list-3" in k
            tag = "ol" if numbered else "ul"
            cls = "list list--numbered" if numbered else "list"
            items = "".join(f"\n  <li>{inline(li.children)}</li>" for li in n.children if isinstance(li, Node))
            self.emit(f'<{tag} class="{cls}">{items}\n</{tag}>')
        elif "grid-5" in k:
            self.requirements(n)
        elif "container-13" in k:
            self.emit('<section class="coda">')
            self.children_indented(n)
            self.emit("</section>")
        elif "container-14" in k or "text-block-34" in k:
            if "container-14" in k:
                self.children(n)
            else:
                self.emit(f'<aside class="afterword">{inline(n.children).replace(ZWJ, "")}</aside>')
        elif is_container(n) or t == "section":
            self.children(n)
        elif t == "div":
            self.children(n)
        else:
            raise ValueError(f"unhandled {t} {k} {text_of(n)[:30]}")

    def children_indented(self, n):
        # emit children one level deeper
        saved = self.out
        self.out = []
        self.children(n)
        inner = ["  " + l for l in self.out]
        self.out = saved + inner

    def requirements(self, n):
        kids = [c for c in n.children if isinstance(c, Node)]
        h_req, h_rec, ul_req, ul_rec = kids  # DOM order: heading, heading, list, list
        def lis(ul):
            return "".join(f"\n      <li>{inline(li.children)}</li>" for li in ul.children if isinstance(li, Node))
        self.emit(
            '<div class="requirements">\n'
            '  <section>\n'
            f'    <h3 class="requirements__title">{inline(h_req.children)}</h3>\n'
            f'    <ul>{lis(ul_req)}\n    </ul>\n'
            '  </section>\n'
            '  <section>\n'
            f'    <h3 class="requirements__title">{inline(h_rec.children)}</h3>\n'
            f'    <ul>{lis(ul_rec)}\n    </ul>\n'
            '  </section>\n'
            '</div>')


def convert_article(slug):
    root = parse(f"{REF}/html/{slug}.html")
    main = root.find_all(lambda n: "section-7" in n.cls)[0]
    a = Article(slug)
    # each top-level container becomes one margin-isolated <div class="block">
    def top_blocks(node):
        for c in node.children:
            if not isinstance(c, Node):
                continue
            if is_container(c):
                yield c
            elif c.tag == "section":
                yield from top_blocks(c)
    blocks = [b for b in top_blocks(main) if text_of(b).strip() or b.find_all(lambda x: x.tag == "img")]
    for b in blocks:
        a.emit('<div class="block">')
        a.children_indented(b)
        a.emit("</div>")
    main_html = "\n".join(a.out)
    # sections after section-7 (goodwill: separate afterword section with its own margins)
    tail = Article(slug)
    for sec in root.find_all(lambda n: "section-10" in n.cls):
        for b in sec.children:
            if isinstance(b, Node):
                tail.emit('<div class="block">')
                tail.children_indented(b)
                tail.emit("</div>")
    return main_html, "\n".join(tail.out)


# ------------------------------------------------------------------ page shell
SITE_URL = "https://konomi.cc"
SVG_MENU = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            '<rect x="4" y="6" width="16" height="2.4"/><rect x="4" y="11" width="16" height="2.4"/>'
            '<rect x="4" y="16" width="16" height="2.4"/></svg>')

FONTS = ("https://fonts.googleapis.com/css2?family=Inconsolata:wght@400;700"
         "&family=Karla:wght@200..800&family=Kiwi+Maru:wght@300;400;500"
         "&family=Noto+Sans+JP:wght@100..900&display=swap")


def meta_for(slug):
    h = open(f"{REF}/html/{'index' if slug == 'index' else slug}.html").read()
    head = h[: h.index("</head>")]
    title = html.unescape(re.search(r"<title>(.*?)</title>", head).group(1))
    desc = html.unescape(re.search(r'<meta content="([^"]*)" name="description"', head).group(1))
    ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', head, re.S).group(1))
    title, desc = META[slug]
    return title, desc, ld


def fix_ld(slug, ld):
    if slug == "index":
        ld.pop("image", None)            # was a template placeholder URL
    if slug == "robot":
        ld["url"] = SITE_URL + "/robot"  # was /astro
    return ld


def header(theme, current):
    brand_cur = ' aria-current="page"' if current == "home" else ""
    def navlink(href, label, key):
        cur = ' aria-current="page"' if current == key else ""
        return f'<a href="{href}"{cur}><span>{label}</span></a>'
    return f'''  <header class="site-header">
    <div class="site-header__inner wrap">
      <a class="brand" href="/"{brand_cur}>
        <span class="brand__name">Konomi <span class="brand__sep" lang="ja">・</span> <span class="brand__jp" lang="ja">中島このみ</span></span>
      </a>
      <nav class="site-nav" aria-label="Main">
        <div class="site-nav__list">{navlink("/about/", "About", "about")}{navlink("/projects/", "Projects", "projects")}</div>
      </nav>
    </div>
  </header>'''


FOOTER = '''  <footer class="site-footer">
    <div class="footer-links wrap">
      <a href="https://www.linkedin.com/in/konomi/" target="_blank" rel="noopener">LinkedIn<span class="visually-hidden"> (opens in a new tab / 新しいタブで開く)</span></a><span class="sep">|</span><a href="https://bsky.app/profile/konomi-n.bsky.social" target="_blank" rel="noopener">bsky<span class="visually-hidden"> (opens in a new tab / 新しいタブで開く)</span></a>
    </div>
  </footer>'''


def page(slug, theme, current, body, lang="en"):
    title, desc, ld = meta_for(slug)
    ld = fix_ld(slug, ld)
    t, d = attr_esc(title), attr_esc(desc)
    url = SITE_URL + ("/" if slug == "index" else f"/{slug}/")
    ldjson = json.dumps(ld, ensure_ascii=False, indent=2).replace("https://www.konomi.cc", SITE_URL)
    return f'''<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="canonical" href="{url}">
  <meta name="description" content="{d}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="{'ja_JP' if any(ord(c) > 0x3000 for c in title) else 'en_US'}">
  <meta property="og:url" content="{url}">
  <meta property="og:site_name" content="Konomi Nakajima | 中島このみ">
  <meta property="og:image" content="{SITE_URL}/images/og-image.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Film photograph of green fields, a lake and distant hills near Schwangau, Germany. ドイツ・シュヴァンガウ近郊の、緑の牧草地と湖、遠くの丘を写したフィルム写真。">
  <meta property="og:title" content="{t}">
  <meta property="og:description" content="{d}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{SITE_URL}/images/og-image.jpg">
  <meta name="twitter:title" content="{t}">
  <meta name="twitter:description" content="{d}">
  <link rel="icon" href="/images/favicon.png">
  <link rel="apple-touch-icon" href="/images/webclip.png">
  <link rel="stylesheet" href="/css/fonts.css">
  <link rel="stylesheet" href="/css/style.css">
  <script type="application/ld+json">
{ldjson}
  </script>
</head>
<body class="theme-{theme}">
  <a class="skip-link" href="#main">Skip to content / 本文へ移動</a>
{header(theme, current)}
{body.replace('<main class="', '<main id="main" class="', 1)}
{FOOTER}
  <script src="/js/main.js" defer></script>
</body>
</html>
'''


def write(slug, content):
    path = f"{SITE}/index.html" if slug == "index" else f"{SITE}/{slug}/index.html"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(content)


# ------------------------------------------------------------------ pages
def build():
    # clean images dir (regenerated each run)
    shutil.rmtree(SITE + "/images", ignore_errors=True)
    os.makedirs(SITE + "/images", exist_ok=True)
    shutil.copy(os.environ["SCRATCH"] + "/og-image.jpg", SITE + "/images/og-image.jpg")  # link-preview image
    for name, orig in (("favicon.png", "6601a2600592a7decad7f951_favicon.png"), ("webclip.png", "6601a2652627e9740ed5dc93_webclip.png")):
        shutil.copy(local_asset(CDN + orig), f"{SITE}/images/{name}")

    trees = {s: parse(f"{REF}/html/{s}.html") for s in IMG_ORDER}
    # --- articles first (they claim shared images)
    bodies = {}
    for slug in ("goodwill", "honda"):
        inner, tail = convert_article(slug)
        bodies[slug] = f'  <main class="article article--column">\n{inner}{chr(10) + tail if tail else ""}\n  </main>'
    # robot
    r = trees["robot"]
    imgs = r.find_all(lambda n: n.tag == "img")
    meta = r.find_all(lambda n: "text-block-5" in n.cls)[0]
    robot = ['<div class="block">', f'  <p class="meta">{inline(meta.children)}</p>']
    robot += ["  " + img_tag(i, "robot", "shot") for i in imgs]
    robot.append("</div>")
    bodies["robot"] = '  <main class="article">\n' + "\n".join("    " + l for l in robot) + "\n  </main>"
    # medium
    m = trees["medium"]
    lead = m.find_all(lambda n: "text-block-5" in n.cls)[0]
    mimg = m.find_all(lambda n: n.tag == "img")[0]
    link = m.find_all(lambda n: n.tag == "a" and "link-6" in n.cls)[0]
    bodies["medium"] = f'''  <main class="article">
    <div class="block">
      <p class="meta">{inline(lead.children)}</p>
      {img_tag(mimg, "medium", "shot")}
      <p class="read-more"><a href="{attr_esc(link.attrs["href"])}" target="_blank" rel="noopener">{inline(link.children)}<span class="visually-hidden"> (opens in a new tab / 新しいタブで開く)</span></a></p>
    </div>
  </main>'''

    # about
    ab = trees["about"]
    abimgs = ab.find_all(lambda n: n.tag == "img")
    caps = [text_of(x).strip() for x in ab.find_all(lambda n: n.cls & {"text-block-46", "text-block-47", "text-block-48"})]
    fig = []
    for i, c in zip(abimgs, caps):
        fig.append(f'''          <figure class="photo">
            {img_tag(i, "about", None, sizes="(max-width: 800px) 26rem, 33vw")}
            <figcaption>{esc(c)}</figcaption>
          </figure>''')
    h1s = [text_of(x).strip() for x in ab.find_all(lambda n: n.tag == "h1")]
    texts = [inline(x.children) for x in ab.find_all(lambda n: n.cls & {"text-block", "text-block-copy"})]
    bodies["about"] = f'''  <main class="about">
    <div class="about__intro wrap">
      <section class="about__col">
        <h1 class="about__title">{esc(h1s[0])}</h1>
        <p class="about__text">{texts[0]}</p>
      </section>
      <section class="about__col about__col--jp" lang="ja">
        <h2 class="about__title">{esc(h1s[1])}</h2>
        <p class="about__text">{texts[1]}</p>
      </section>
    </div>
  </main>
  <section class="photos">
    <div class="wrap">
      <div class="photos__grid">
{chr(10).join(fig)}
      </div>
    </div>
  </section>'''

    # index
    ix = trees["index"]
    hero = ix.find_all(lambda n: n.tag == "img")[0]
    cap = text_of(ix.find_all(lambda n: "text-block-12" in n.cls)[0]).strip()
    tag_en = text_of(ix.find_all(lambda n: "text-block-18" in n.cls)[0]).strip()
    jp = inline(ix.find_all(lambda n: "text-block-20" in n.cls)[0].children)
    bodies["index"] = f'''  <main class="home">
    <div class="home__grid wrap">
      <h1 class="home__title">{esc(tag_en)}</h1>
      <p class="home__title-jp" lang="ja">{jp}</p>
      <figure class="home__figure">
        {img_tag(hero, "home", "home__photo", width=381, loading="eager", sizes="(max-width: 767px) 50vw, 381px")}
        <figcaption class="home__caption">{esc(cap)}</figcaption>
      </figure>
    </div>
  </main>'''

    # projects
    pr = trees["projects"]
    rows = pr.find_all(lambda n: "columns-2" in n.cls)
    out = []
    for row in rows:
        cols = [c for c in row.children if isinstance(c, Node)]
        a_el = cols[0].find_all(lambda n: n.tag == "a")[0]
        im = cols[0].find_all(lambda n: n.tag == "img")[0]
        href = href_map(a_el.attrs["href"])
        text_div = cols[1].find_all(lambda n: n.cls & {"text-block-8", "text-block-9", "text-block-10", "text-block-11"})[0]
        raw = inline(text_div.children)
        blurb, tags = re.split(r"(?:<br>)+", raw, maxsplit=1)
        trans = cols[1].find_all(lambda n: "text-block-38" in n.cls)
        tr_html = ""
        if trans:
            ta = trans[0].find_all(lambda n: n.tag == "a")[0]
            tr_html = (f'\n          <p class="project__translation" lang="ja"><a href="{href_map(ta.attrs["href"])}">'
                       f'<b>*</b> <span>日本語訳あり</span></a></p>')
        alt = im.attrs.get("alt", "")
        out.append(f'''        <article class="project">
          <a href="{href}">
            {img_tag(im, "projects", None)}
          </a>
          <div class="project__text">
            <p class="project__blurb">{blurb.strip()}</p>
            <p class="project__tags">{tags.strip()}</p>{tr_html}
          </div>
        </article>''')
    bodies["projects"] = f'''  <main class="projects">
    <div class="wrap">
{chr(10).join(out)}
    </div>
  </main>'''

    # ai-process
    ap = trees["ai-process"]
    g = lambda c: ap.find_all(lambda n: c in n.cls)[0]
    jp_body = paragraphs(inline(g("body-article").children))
    en_body = paragraphs(inline(g("text-block-40").children).replace("<br><br>", "<br><br>"))
    aside_jp = inline(g("text-block-45").children)
    aside_en = inline(g("text-block-43").children)
    bodies["ai-process"] = f'''  <main class="article article--column">
    <div class="block" lang="ja">
      <h1 class="ai-jp-title">{inline(g("text-block-44").children)}</h1>
      <p class="ai-jp-sub">{inline(g("text-block-49").children)}</p>
      <div class="prose">
        {jp_body.replace(chr(10), chr(10) + "        ")}
      </div>
      <p class="ai-jp-aside">{aside_jp}</p>
    </div>
    <div class="block" lang="en">
      <h2 class="ai-en-title">{inline(g("text-block-39").children)}</h2>
      <p class="ai-en-sub">{inline(g("text-block-50").children)}</p>
      <div class="ai-en-body">
        {en_body.replace(chr(10), chr(10) + "        ")}
      </div>
    </div>
    <div class="block" lang="en">
      <p class="ai-en-aside">{aside_en}</p>
    </div>
  </main>'''

    for slug in ("robot", "medium"):
        bodies[slug] = bodies[slug].replace('<main class="article">', '<main class="article article--column">', 1)

    meta_theme = {"index": ("dark", "home", "en"), "about": ("dark", "about", "en"), "projects": ("dark", "projects", "en"),
                  "goodwill": ("light", None, "ja"), "honda": ("light", None, "ja"), "robot": ("light", None, "en"),
                  "medium": ("light", None, "en"), "ai-process": ("light", None, "ja")}
    for slug, (theme, cur, lang) in meta_theme.items():
        write(slug, page(slug, theme, cur, bodies[slug], lang))
    print("built", len(meta_theme), "pages;", len(img_by_md5), "images")


if __name__ == "__main__":
    build()
