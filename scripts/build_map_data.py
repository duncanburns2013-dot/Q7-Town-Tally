"""Project + simplify Census MA town boundaries, join the Q7/enrollment table,
and inject the result into the page template.

Usage: .venv/Scripts/python scripts/build_map_data.py
"""
import csv
import json
import math
import re
from pathlib import Path

import shapefile
from shapely.geometry import shape, mapping
from shapely.ops import transform

ROOT = Path(__file__).resolve().parent.parent
SHP = ROOT / "raw/census/cb_2023_25_cousub_500k"
TABLE = ROOT / "q7_by_town_with_enrollment.csv"
TEMPLATE = ROOT / "site/template.html"
OUT = ROOT / "site/q7-town-map.html"
PAGES = ROOT / "index.html"
OG_TEMPLATE = ROOT / "site/og-template.html"
OG_PAGE = ROOT / "og.html"

# Social preview tags for the GitHub Pages copy. og:image must be an absolute URL.
SITE = "https://duncanburns2013-dot.github.io/Q7-Town-Tally/"
_SOC_TITLE = "Question 7, town by town"
_SOC_DESC = ("How each of Massachusetts' 351 cities and towns voted on Question 7 "
             "(5,000 sq ft minimum lots), mapped beside party enrollment. Unofficial results.")
_SOC_ALT = ("Map of Massachusetts towns shaded from cranberry (No) to green (Yes) on Question 7; "
            "No {np:.1f}%, Yes {yp:.1f}%, unofficial.")
SOCIAL = (
    f'<link rel="canonical" href="{SITE}">\n'
    '<meta property="og:type" content="website">\n'
    f'<meta property="og:url" content="{SITE}">\n'
    f'<meta property="og:title" content="{_SOC_TITLE}">\n'
    f'<meta property="og:description" content="{_SOC_DESC}">\n'
    f'<meta property="og:image" content="{SITE}og.png">\n'
    '<meta property="og:image:width" content="1200">\n'
    '<meta property="og:image:height" content="630">\n'
    f'<meta property="og:image:alt" content="{_SOC_ALT}">\n'
    '<meta name="twitter:card" content="summary_large_image">\n'
    f'<meta name="twitter:title" content="{_SOC_TITLE}">\n'
    f'<meta name="twitter:description" content="{_SOC_DESC}">\n'
    f'<meta name="twitter:image" content="{SITE}og.png">\n'
    f'<meta name="twitter:image:alt" content="{_SOC_ALT}">\n'
)

LAT0 = 42.1
K = math.cos(math.radians(LAT0))
W = 1000.0  # viewBox width


def key(name):
    n = name.lower()
    n = re.sub(r"\s+town$", "", n)  # Census "Barnstable Town", "Agawam Town" ...
    return re.sub(r"[^a-z]", "", n)


def main():
    rows = {key(r["town"]): r for r in csv.DictReader(open(TABLE, encoding="utf-8"))}
    sf = shapefile.Reader(str(SHP))
    geoms = {}
    for sr in sf.shapeRecords():
        rec = sr.record.as_dict()
        k = key(rec["NAME"])
        assert k in rows, f"no table row for Census town {rec['NAME']!r}"
        assert k not in geoms, f"duplicate {k}"
        cty = rec["NAMELSADCO"].replace(" County", "")
        assert cty == rows[k]["county"], f"county mismatch {k}: {cty} vs {rows[k]['county']}"
        geoms[k] = shape(sr.shape.__geo_interface__)
    assert set(geoms) == set(rows), sorted(set(rows) ^ set(geoms))

    # Projection: equirectangular scaled by cos(lat0), fitted to W.
    allb = [g.bounds for g in geoms.values()]
    minx = min(b[0] for b in allb) * K
    maxx = max(b[2] for b in allb) * K
    miny = min(b[1] for b in allb)
    maxy = max(b[3] for b in allb)
    s = W / (maxx - minx)
    H = (maxy - miny) * s

    def proj(x, y, z=None):
        return ((x * K - minx) * s, (maxy - y) * s)

    def path(g):
        parts = []
        polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
        for p in polys:
            for ring in [p.exterior, *p.interiors]:
                pts = list(ring.coords)
                if len(pts) < 4:
                    continue
                d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts[:-1]) + "Z"
                parts.append(d)
        return "".join(parts)

    towns = []
    for k, g in geoms.items():
        r = rows[k]
        pg = transform(proj, g)
        simp = pg.simplify(0.35, preserve_topology=True)
        # drop specks (tiny islands) that would not render anyway
        if simp.geom_type == "MultiPolygon":
            keep = [p for p in simp.geoms if p.area > 0.6] or [max(simp.geoms, key=lambda p: p.area)]
            from shapely.geometry import MultiPolygon
            simp = MultiPolygon(keep) if len(keep) > 1 else keep[0]
        c = pg.representative_point()
        towns.append({
            "n": r["town"], "c": r["county"],
            "reg": int(r["registered"]), "d": int(r["democrat"]), "r": int(r["republican"]),
            "u": int(r["unenrolled"]), "o": int(r["other"]),
            "y": int(r["q7_yes"]), "no": int(r["q7_no"]),
            "pr": int(r["precincts_reporting"]), "pt": int(r["precincts_total"]),
            "x": round(c.x, 1), "cy": round(c.y, 1),
            "p": path(simp),
        })
    towns.sort(key=lambda t: t["n"])

    # Figure checks against the source totals before anything is written.
    assert len(towns) == 351
    assert sum(t["y"] for t in towns) == 1255595
    assert sum(t["no"] for t in towns) == 1287917
    assert sum(t["reg"] for t in towns) == 5025826
    assert sum(t["d"] for t in towns) == 1298603
    assert sum(t["r"] for t in towns) == 423387
    assert sum(t["u"] for t in towns) == 3254435
    assert sum(t["o"] for t in towns) == 49401

    ty, tn = sum(t['y'] for t in towns), sum(t['no'] for t in towns)
    np, yp = 100 * tn / (ty + tn), 100 * ty / (ty + tn)

    data = {"w": W, "h": round(H, 1), "towns": towns}
    js = json.dumps(data, separators=(",", ":"))
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", js)
    assert "/*__DATA__*/" not in html
    OUT.write_text(html, encoding="utf-8")
    print(f"{len(towns)} towns, viewBox {W:.0f}x{H:.0f}, page {len(html)/1024:.0f} KB -> {OUT}")

    # Standalone copy for GitHub Pages: the artifact host supplies the document
    # skeleton itself, a plain static host does not.
    head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<meta name="description" content="Massachusetts 2026 Question 7 (minimum lot '
            'sizes) results by city and town, alongside party enrollment.">\n'
            + SOCIAL.replace('{np:.1f}', f'{np:.1f}').replace('{yp:.1f}', f'{yp:.1f}'))
    page = html.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    assert page.startswith("<title>")
    assert page.count("</style>") == 1
    PAGES.write_text(head + page.replace("</style>", "</style>\n</head>\n<body>", 1)
                     + "\n</body>\n</html>\n", encoding="utf-8")
    print(f"pages copy -> {PAGES}")

    # Social card source (rendered to og.png separately). It must paint with the
    # exact ramp the page uses.
    og = OG_TEMPLATE.read_text(encoding="utf-8")
    div = re.search(r"const DIV = \[[^\]]*\];", html).group(0)
    assert div in og, "og-template DIV ramp differs from the page"
    og = og.replace("/*__DATA__*/null", js)
    assert "/*__DATA__*/" not in og
    OG_PAGE.write_text(og, encoding="utf-8")
    print(f"og card -> {OG_PAGE}")


if __name__ == "__main__":
    main()
