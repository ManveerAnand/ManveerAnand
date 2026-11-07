"""Draw the animated section headings in assets/headings/.

Run after changing a title: python .github/scripts/headings.py
"""
import os
from html import escape

# (file, title, note on the right, two palette colours the title cycles through)
HEADINGS = [
    ("projects", "Brightest stars", "what I've shipped", "779dff", "c084fc"),
    ("stack", "Tech Stack", "what I build with", "5eead4", "8ed345"),
    ("stats", "GitHub Stats", "live from GitHub", "fcca1b", "ff7a90"),
    ("vibe", "Vibe with me", "on repeat", "ff7a90", "c084fc"),
    ("connect", "Connect", "say hi", "c084fc", "5eead4"),
]


def svg(i, title, note, a, b):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="48" viewBox="0 0 800 48" role="img">
<title>{escape(title)}</title>
<defs><linearGradient id="g" x1="0" x2="1">
<stop class="s1" offset="0" stop-color="#{a}"/><stop class="s2" offset="1" stop-color="#{b}"/>
</linearGradient></defs>
<style>
.s1{{animation:c1 4s ease-in-out infinite alternate}}
.s2{{animation:c2 4s ease-in-out infinite alternate}}
@keyframes c1{{to{{stop-color:#{b}}}}}
@keyframes c2{{to{{stop-color:#{a}}}}}
.ring{{transform-box:fill-box;transform-origin:center;animation:ping 2.4s ease-out infinite}}
@keyframes ping{{from{{transform:scale(.6);opacity:.9}}to{{transform:scale(2.4);opacity:0}}}}
.cur{{animation:blink 1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.s1,.s2,.ring,.cur{{animation:none}}}}
.mono{{font-family:'JetBrains Mono',ui-monospace,Consolas,monospace}}
</style>
<circle class="ring" cx="10" cy="26" r="6" fill="none" stroke="#{a}" stroke-width="2"/>
<circle cx="10" cy="26" r="5" fill="#{a}"/>
<text class="mono" x="26" y="31" font-size="13" fill="#{a}">{i:02d}</text>
<text x="54" y="35" font-family="-apple-system,'Segoe UI',Helvetica,Arial,sans-serif" font-size="28" font-weight="700" fill="url(#g)">{escape(title)}</text>
<text class="mono" x="790" y="32" font-size="12" text-anchor="end" fill="#93a6c4">// {escape(note)}<tspan class="cur" fill="#{b}">_</tspan></text>
</svg>
'''


out = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "headings")
os.makedirs(out, exist_ok=True)
for i, (file, title, note, a, b) in enumerate(HEADINGS, 1):
    with open(os.path.join(out, f"{file}.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg(i, title, note, a, b))
    print(f"{file}.svg")
