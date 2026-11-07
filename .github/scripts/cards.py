"""Cut the GitSkins project grid into one card per repo, with a language ring
and chips drawn from GitHub's own language data so the two always agree.

Usage: python cards.py <dir holding projects.svg>   (needs GITHUB_TOKEN)
"""
import json
import math
import os
import re
import sys
import urllib.request
from html import escape

USER = "ManveerAnand"
# (output name, repo, card origin in the 860x452 grid)
CARDS = [
    ("voicelink", "VoiceLink", (28, 88)),
    ("bolbot", "BOLBOT", (438, 88)),
    ("river-atlas", "india-river-atlas", (28, 266)),
    ("articulate3d", "articulate3D", (438, 266)),
]
ROOT = 'width="860" height="452" viewBox="0 0 860 452"'
R, CIRC = 25, 2 * math.pi * 25
MONO = "ui-monospace,'SF Mono',Consolas,monospace"

# GitSkins' own chips (topics or one language) and ring, which we redraw.
STRIP = [
    r'<rect x="[^"]*" y="112" width="[^"]*" height="18" rx="9"[^>]*/>',
    r'<text x="[^"]*" y="124\.5"[^>]*>[^<]*</text>',
    r'<circle cx="348" cy="92"[^>]*/>',
    r'<circle cx="348" cy="92"[^>]*>.*?</circle>',
    r'<text x="348" y="96"[^>]*>[^<]*</text>',
]


def languages():
    """{repo: [(name, color, share), ...]} largest first."""
    parts = " ".join(
        f'r{i}: repository(owner:"{USER}", name:"{repo}") '
        "{ languages(first:10, orderBy:{field:SIZE, direction:DESC}) "
        "{ totalSize edges { size node { name color } } } }"
        for i, (_, repo, _) in enumerate(CARDS))
    req = urllib.request.Request(
        "https://api.github.com/graphql", json.dumps({"query": "{" + parts + "}"}).encode(),
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "User-Agent": "profile-readme-cards"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)["data"]
    out = {}
    for i, (_, repo, _) in enumerate(CARDS):
        langs = data[f"r{i}"]["languages"]
        total = langs["totalSize"] or 1
        out[repo] = [(e["node"]["name"], e["node"]["color"] or "#8b949e", e["size"] / total)
                     for e in langs["edges"]]
    return out


def ring(cx, cy, langs):
    shown = langs[:4]
    rest = 1 - sum(s for _, _, s in shown)
    if rest > 0.005:
        shown = shown + [("Other", "#6e7681", rest)]
    out = [f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#a5b4fc" stroke-opacity=".18" stroke-width="8"/>']
    start = 0.0
    for i, (_, color, share) in enumerate(shown):
        seg = share * CIRC
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{color}" stroke-width="8" '
            f'stroke-dasharray="{seg:.2f} {CIRC - seg:.2f}" transform="rotate({start * 360 - 90:.2f} {cx} {cy})">'
            f'<animate attributeName="stroke-dasharray" from="0 {CIRC:.2f}" to="{seg:.2f} {CIRC - seg:.2f}" '
            f'dur=".6s" begin="{0.8 + i * 0.15:.2f}s" fill="freeze"/></circle>')
        start += share
    top = langs[0][2] * 100 if langs else 0
    out.append(f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-family="{MONO}" font-size="11" '
               f'font-weight="700" fill="#e0e7ff">{top:.0f}%</text>')
    return "".join(out)


def chips(x0, y, langs):
    out, x = [], x0
    for i, (name, color, share) in enumerate(langs):
        label = f"{name} {share * 100:.0f}%"
        w = 22 + 5.1 * len(label)
        more = f"+{len(langs) - i} more"
        # Leave room for a "+N more" chip unless this is the last language.
        limit = x0 + 282 - (0 if i == len(langs) - 1 else 8 + 5.1 * len(more))
        if x + w > limit:
            out.append(f'<text x="{x + 4:.1f}" y="{y + 12.5}" font-family="{MONO}" font-size="8.5" '
                       f'fill="#a5b4fc" fill-opacity=".7">{more}</text>')
            break
        out.append(
            f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="18" rx="9" fill="{color}" fill-opacity=".14" '
            f'stroke="{color}" stroke-opacity=".55"/>'
            f'<circle cx="{x + 10:.1f}" cy="{y + 9}" r="3.5" fill="{color}" stroke="#c7d2fe" stroke-width=".6"/>'
            f'<text x="{x + 17:.1f}" y="{y + 12.5}" font-family="{MONO}" font-size="8.5" fill="#c7d2fe">'
            f'{escape(label)}</text>')
        x += w + 5
    return "".join(out)


def build(grid, langs_by_repo, out_dir):
    if ROOT not in grid:
        raise SystemExit("projects.svg layout changed")
    base = grid
    for pat in STRIP:
        base = re.sub(pat, "", base, flags=re.S)
    for name, repo, (x, y) in CARDS:
        langs = langs_by_repo[repo]
        svg = base.replace(ROOT, f'width="406" height="174" viewBox="{x - 6} {y - 6} 406 174"')
        extra = ring(x + 348, y + 92, langs) + chips(x + 18, y + 112, langs)
        svg = svg.replace("</svg>", extra + "</svg>")
        with open(os.path.join(out_dir, f"card-{name}.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"card-{name}.svg  " + ", ".join(f"{n} {s * 100:.0f}%" for n, _, s in langs))


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "dist"
    with open(os.path.join(d, "projects.svg"), encoding="utf-8") as f:
        grid = f.read()
    leftovers = sum(len(re.findall(p, grid, flags=re.S)) for p in STRIP[-1:])
    assert leftovers == 4, f"expected 4 ring labels in projects.svg, found {leftovers}"
    build(grid, languages(), d)
