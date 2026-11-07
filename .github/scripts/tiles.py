"""Build the animated tech stack tiles for the profile README.

Each tile reuses the logo GitSkins draws, then adds the repo it links to and a
live number from the GitHub API: a language's share of all my public code, or
a count for tools. Usage: python tiles.py <out-dir>
GITHUB_TOKEN is optional locally; without it the commit count is left out.
"""
import base64
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from html import escape

USER = "ManveerAnand"
TOKEN = os.environ.get("GITHUB_TOKEN")

# (file, logo, caption, color, language whose share fills the bar, or a tool stat key)
TILES = [
    ("python", "Python", "VoiceLink", "fcca1b", "Python"),
    ("typescript", "TypeScript", "BOLBOT", "779dff", "TypeScript"),
    ("c", "C", "multiserver", "5eead4", "C"),
    ("cpp", "C++", "VoiceLink", "c084fc", "C++"),
    ("go", "Go", "reverse proxy", "8ed345", "Go"),
    ("bash", "Bash", "multiserver", "ff7a90", "Shell"),
    ("node-js", "Node.js", "BOLBOT runtime", "5eead4", None),
    ("git", "Git", "commits this year", "ff7a90", "commits"),
    ("github", "GitHub", "public repos", "c084fc", "repos"),
]


def get(url, data=None):
    headers = {"User-Agent": "profile-readme-tiles"}
    # Only GitHub gets the token; the logo requests go to gitskins.com.
    if TOKEN and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def gh(path):
    return json.loads(get("https://api.github.com" + path))


def stats():
    repos = [r for r in gh(f"/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
    totals = {}
    for r in repos:
        for lang, n in gh(f"/repos/{USER}/{r['name']}/languages").items():
            totals[lang] = totals.get(lang, 0) + n
    code = sum(totals.values())
    share = {k: v / code for k, v in totals.items()}
    if not TOKEN:  # GraphQL needs auth
        return share, {"repos": len(repos)}
    q = '{user(login:"%s"){contributionsCollection{totalCommitContributions}}}' % USER
    res = json.loads(get("https://api.github.com/graphql", json.dumps({"query": q}).encode()))
    commits = res["data"]["user"]["contributionsCollection"]["totalCommitContributions"]
    return share, {"commits": commits, "repos": len(repos)}


def logo(name):
    url = ("https://www.gitskins.com/api/readme-reference/technology-stack?username=manveeranand"
           f"&theme=midnight&logos={urllib.parse.quote(name)}&v={int(time.time())}")
    svg = get(url).decode()
    m = re.search(r'<image href="(data:image/[^"]+)"', svg)
    if not m:
        raise SystemExit(f"no logo found for {name}")
    return m.group(1)


def tile(i, logo_href, label, caption, color, value, text):
    delay = f"{i * 0.35:.2f}s"
    bar = ""
    if value is not None:
        w = max(4.0, 96 * value)
        bar = (f'<rect x="12" y="98" width="96" height="5" rx="2.5" fill="#1a2238"/>'
               f'<rect class="fill" x="12" y="98" width="{w:.1f}" height="5" rx="2.5" fill="#{color}"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="120" height="112" viewBox="0 0 120 112" role="img">
<title>{escape(label)}: {escape(caption)}</title>
<style>
.glow{{animation:glow 3s ease-in-out {delay} infinite}}
.logo{{animation:bob 3s ease-in-out {delay} infinite}}
.fill{{transform-box:fill-box;transform-origin:left;animation:grow 1.4s ease-out {delay} both}}
@keyframes glow{{0%,100%{{stroke-opacity:.55}}50%{{stroke-opacity:1}}}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-3px)}}}}
@keyframes grow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@media (prefers-reduced-motion:reduce){{.glow,.logo,.fill{{animation:none}}}}
text{{font-family:'JetBrains Mono',ui-monospace,Consolas,monospace;text-anchor:middle}}
</style>
<rect x="1" y="1" width="118" height="110" rx="12" fill="#0f1424"/>
<rect class="glow" x="1" y="1" width="118" height="110" rx="12" fill="none" stroke="#{color}" stroke-width="2"/>
<g class="logo"><image href="{logo_href}" x="40" y="10" width="40" height="40" preserveAspectRatio="xMidYMid meet"/></g>
<text x="60" y="66" font-size="12" font-weight="700" fill="#edf4ff">{escape(label)}</text>
<text x="60" y="81" font-size="9" fill="#{color}">{escape(text)}</text>
{bar}
</svg>'''


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "dist"
    os.makedirs(out, exist_ok=True)
    share, counts = stats()
    for i, (file, name, caption, color, key) in enumerate(TILES):
        if key in ("commits", "repos") and key not in counts:
            value, text = None, caption
        elif key in counts:
            value, text = None, f"{counts[key]} {caption}"
        elif key:
            value = share.get(key, 0)
            text = f"{caption} · {value * 100:.0f}%"
        else:
            value, text = None, caption
        svg = tile(i, logo(name), name, caption, color, value, text)
        with open(os.path.join(out, f"tile-{file}.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"tile-{file}.svg  {text}")


if __name__ == "__main__":
    main()
