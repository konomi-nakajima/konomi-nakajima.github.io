"""Insert <wbr> at Japanese phrase boundaries in headings (uses Google's BudouX).
Run after build.py and optimize.py:   python phrases.py   (needs: pip install budoux)
Together with the .jp-phrases CSS rule this makes headings break between phrases in every browser."""
import re, glob, budoux

SITE = "/Users/konomi/Documents/portfolio-site/site"
parser = budoux.load_default_japanese_parser()
CLASSES = r"article-title|article-subtitle|section-title|ai-jp-title|ai-jp-sub|home__title-jp|about__title"
pat = re.compile(r'<(h1|h2|p) class="((?:%s))"([^>]*)>(.*?)</\1>' % CLASSES, re.S)
has_jp = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")

def segment(inner):
    # keep tags such as <br> as they are; segment the text pieces between them
    parts = re.split(r"(<[^>]+>)", inner)
    return "".join(p if p.startswith("<") else "<wbr>".join(parser.parse(p)) for p in parts)

def fix(m):
    tag, cls, rest, inner = m.groups()
    if not has_jp.search(inner) or "<wbr>" in inner:
        return m.group(0)
    return f'<{tag} class="{cls} jp-phrases"{rest}>{segment(inner)}</{tag}>'

for f in glob.glob(SITE + "/**/index.html", recursive=True):
    t = open(f).read()
    t2 = pat.sub(fix, t)
    if t2 != t:
        open(f, "w").write(t2)
