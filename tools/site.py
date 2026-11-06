#!/usr/bin/env python3
"""SPAN 1001 site: build the index pages from site.json, check the site, roll a term over.

    python3 tools/site.py build                  # writes index.html, current/index.html, archive/*/index.html, 404.html
    python3 tools/site.py check                  # links exist, nothing forbidden is on the site (build runs it too)
    python3 tools/site.py rollover spring-2027-mwf "Spring 2027" MWF "Monday, Wednesday & Friday"
        # current/ -> archive/fall-2026-tr/, starts an empty current/ for the new term, rebuilds

Pages under current/ are self-contained (their own CSS/JS), so they keep working after they move to archive/.
Only the generated index pages use assets/kit/. Standard library only.
"""
import html, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site.json"

# Never on this public site (see README): exams, keys, grading tools, rosters, student work.
FORBIDDEN_NAME = re.compile(r"(grading|answer[-_]?key|[-_]key\b|roster|gradebook|corrections?[-_]key|exam\d*[-_]v[a-d]|\.tex$|\.csv$|\.xlsx?$|\.zip$)", re.I)
FORBIDDEN_TEXT = [re.compile(p, re.I) for p in (r"@ung\.edu", r"\b9\d{8}\b", r"answer key", r"localStorage\.setItem\(['\"]\w*grad")]

e = lambda s: html.escape(str(s), quote=True)


def load():
    return json.loads(SITE.read_text(encoding="utf8"))


def head(title, desc, depth):
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Source+Serif+4:ital,wght@0,600;0,700;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/kit/kit.css">
<script src="{up}assets/kit/kit.js"></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""


def mast(course, crumbs, kicker, h1, sub, card):
    cr = ' <span aria-hidden="true">/</span> '.join(
        f'<a href="{e(h)}">{e(t)}</a>' if h else f'<span aria-current="page">{e(t)}</span>' for t, h in crumbs)
    dl = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in card)
    return f"""<header class="mast">
  <div class="wrap mast-top">
    <nav class="crumbs" aria-label="Breadcrumb">{cr}</nav>
    <div class="tools">
      <button type="button" class="tbtn" id="theme-btn" onclick="toggleTheme()" aria-pressed="false">Dark mode</button>
      <button type="button" class="tbtn" id="fs-btn" onclick="toggleFS()">Full screen</button>
    </div>
  </div>
  <div class="wrap mast-body">
    <div>
      <p class="kicker">{e(kicker)}</p>
      <h1>{e(h1)}</h1>
      <p class="sub" lang="es">{e(sub)}</p>
    </div>
    <dl class="term-card">{dl}</dl>
  </div>
</header>
"""


def sections_html(term, prefix):
    if not term["sections"]:
        return '<p class="empty">Nothing posted for this term yet.</p>'
    out = []
    for s in term["sections"]:
        items = []
        for it in s["items"]:
            tags = f'<span class="tag">{e(it.get("kind", "Page"))}</span>'
            if it.get("audience") == "instructor":
                tags += '<span class="tag instructor">Instructor</span>'
            items.append(f"""      <li class="item"><a href="{e(prefix + it['path'])}">
        <span class="t">{e(it['title'])}</span>
        <span class="d">{e(it.get('desc', ''))}</span>
        <span class="meta">{tags}<span class="go" aria-hidden="true">→</span></span>
      </a></li>""")
        w = s.get("when") or {}
        rail = (f'<p class="rail"><span class="m">{e(w.get("month", ""))}</span><span class="dd">{e(w.get("days", ""))}</span></p>'
                if w else '<p class="rail" aria-hidden="true"></p>')
        out.append(f"""  <section class="section" id="{e(s['id'])}" aria-labelledby="h-{e(s['id'])}">
    {rail}
    <div class="sec-body">
    <div class="sec-head"><h2 id="h-{e(s['id'])}">{e(s['title'])}<span class="es" lang="es">{e(s.get('titleEs', ''))}</span></h2></div>
    <ul class="items">
{chr(10).join(items)}
    </ul>
    </div>
  </section>""")
    return "\n".join(out)


def aside(site, depth, here):
    up = "../" * depth
    terms = [f'<li><a href="{up}current/">{e(site["current"]["term"])} · {e(site["current"]["schedule"])}</a> (current)</li>']
    terms += [f'<li><a href="{up}archive/{e(t["id"])}/">{e(t["term"])} · {e(t["schedule"])}</a></li>' for t in site["archive"]]
    return f"""<aside aria-label="About this site">
  <div class="box"><h2>Terms</h2><ul>{''.join(terms)}</ul></div>
  <div class="box"><h2>About</h2>
    <p>Class pages and tools for {e(site['course']['code'])}. Your grades, feedback and submissions are in D2L, not here.</p>
    <p>No student data is stored on this site.</p></div>
</aside>"""


def footer(site):
    c = site["course"]
    return f"""<footer><div class="wrap">{e(c['code'])} · {e(c['title'])} · {e(c['institution'])}</div></footer>
</body>
</html>
"""


def term_page(site, term, depth, is_current, root_page=False):
    c = site["course"]
    prefix = "current/" if root_page else ""
    label = f"{term['term']} · {term['schedule']}"
    if root_page:
        crumbs = [(c["code"], None)]
        kicker = f"Current term · {label}"
    else:
        crumbs = [(c["code"], "../" * depth), (label, None)]
        kicker = ("Current term · " if is_current else "Archived term · ") + label
    card = [("Term", term["term"]), ("Meets", term.get("scheduleLong", term["schedule"]))]
    if not is_current:
        card.append(("Status", "Archived"))
    title = f"{c['code']} · {label}"
    return (head(title, f"{c['code']} {c['title']}: pages and tools for {label}.", depth)
            + mast(c, crumbs, kicker, c["code"], c["titleEs"], card)
            + f'<main id="main"><div class="wrap layout">\n<div>\n{sections_html(term, prefix)}\n</div>\n'
            + aside(site, depth, term["id"]) + "\n</div></main>\n" + footer(site))


def page_404(site):
    c = site["course"]
    return (head(f"Page not found · {c['code']}", "This page moved or no longer exists.", 0).replace('href="assets/', 'href="/span1001/assets/').replace('src="assets/', 'src="/span1001/assets/')
            + mast(c, [(c["code"], "/span1001/"), ("Not found", None)], "404", "Page not found", "Esta página no existe.", [("Course", c["code"])])
            + '<main id="main"><div class="wrap"><p>This page moved or was removed at the end of a term. '
            + '<a href="/span1001/">Go to the course home</a> for the current pages.</p></div></main>\n' + footer(site))


def build():
    site = load()
    cur = site["current"]
    (ROOT / "current").mkdir(exist_ok=True)
    (ROOT / "index.html").write_text(term_page(site, cur, 0, True, root_page=True), encoding="utf8")
    (ROOT / "current/index.html").write_text(term_page(site, cur, 1, True), encoding="utf8")
    for t in site["archive"]:
        d = ROOT / "archive" / t["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(term_page(site, t, 2, False), encoding="utf8")
    (ROOT / "404.html").write_text(page_404(site), encoding="utf8")
    print("built: index.html, current/index.html, 404.html" + "".join(f", archive/{t['id']}/index.html" for t in site["archive"]))
    return check()


def check():
    site, bad = load(), []
    terms = [("current", site["current"])] + [(f"archive/{t['id']}", t) for t in site["archive"]]
    for folder, t in terms:
        for s in t["sections"]:
            for it in s["items"]:
                if not (ROOT / folder / it["path"]).is_file():
                    bad.append(f"missing: {folder}/{it['path']} (listed in site.json)")
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT).as_posix()
        if p.is_dir() or rel.startswith((".git/", "tools/")) or rel == "README.md":
            continue
        if FORBIDDEN_NAME.search(p.name):
            bad.append(f"forbidden file type/name: {rel}")
        if p.suffix in (".html", ".js", ".json", ".md", ".css"):
            txt = p.read_text(encoding="utf8", errors="ignore")
            for rx in FORBIDDEN_TEXT:
                if rx.search(txt):
                    bad.append(f"forbidden content ({rx.pattern}): {rel}")
    for b in bad:
        print("  ✗", b)
    print("check: OK" if not bad else f"check: {len(bad)} problem(s)")
    return 0 if not bad else 1


def rollover(new_id, term, schedule, schedule_long):
    site = load()
    old = site["current"]
    dest = ROOT / "archive" / old["id"]
    if dest.exists():
        sys.exit(f"archive/{old['id']} already exists")
    if not re.fullmatch(r"(spring|summer|fall)-\d{4}-(mwf|tr|mw|online)", new_id):
        sys.exit("term id must look like spring-2027-mwf or fall-2027-tr")
    dest.parent.mkdir(exist_ok=True)
    try:
        subprocess.run(["git", "mv", "current", str(dest.relative_to(ROOT))], cwd=ROOT, check=True)
    except Exception:
        shutil.move(str(ROOT / "current"), str(dest))
    site["archive"].insert(0, old)
    site["current"] = {"id": new_id, "term": term, "schedule": schedule, "scheduleLong": schedule_long, "sections": []}
    SITE.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(f"archived {old['id']}; current = {new_id}")
    return build()


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["build"]:
        sys.exit(build())
    if a[:1] == ["check"]:
        sys.exit(check())
    if a[:1] == ["rollover"] and len(a) == 5:
        sys.exit(rollover(*a[1:]))
    sys.exit(__doc__)
