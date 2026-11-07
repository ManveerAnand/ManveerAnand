#!/usr/bin/env bash
# Fetch the GitSkins images for the profile README and strip their branding.
# Usage: skins.sh <out-dir>
set -euo pipefail
out="${1:-dist}"
mkdir -p "$out"

A='avatar=https%3A%2F%2Favatars.githubusercontent.com%2Fu%2F128989083%3Fv%3D4'
B='https://www.gitskins.com/api/section'

fetch() { # name url
  # A fresh v= skips GitSkins' edge cache, which otherwise serves day-old data.
  curl -fsSL --retry 3 "$2&v=$(date +%s)" -o "$out/$1.svg"
  # Drop the corner "gitskins.com" mark and rename the hero label.
  sed -i -E \
    -e 's#<text[^>]*>gitskins\.com</text>##g' \
    -e 's#GITSKINS / LIVING IDENTITY#MANVEER ANAND / LIVE#g' \
    "$out/$1.svg"
  ! grep -qi '>gitskins' "$out/$1.svg" || { echo "branding left in $1.svg" >&2; exit 1; }
  grep -q '<svg' "$out/$1.svg" || { echo "$1.svg is not an SVG" >&2; exit 1; }
}

fetch hero     "$B/hero?username=manveeranand&theme=midnight&$A&variant=living-identity&label=Manveer%20Anand&mode=dark"
fetch galaxy   "$B/galaxy?username=manveeranand&theme=midnight&$A"
fetch projects "$B/projects?username=manveeranand&theme=midnight&$A&repos=manveeranand%2FVoiceLink%2Cmanveeranand%2FBOLBOT%2Cmanveeranand%2Findia-river-atlas%2Cmanveeranand%2Farticulate3D"

# Crop the 2x2 project grid into one image per card so each can link to its repo.
# Cards are 394x162 at (28,88) (438,88) (28,266) (438,266); keep a 6px margin.
root='width="860" height="452" viewBox="0 0 860 452"'
grep -q "$root" "$out/projects.svg" || { echo "projects.svg layout changed" >&2; exit 1; }
for card in "voicelink 22 82 VoiceLink" "bolbot 432 82 BOLBOT" "river-atlas 22 260 india-river-atlas" "articulate3d 432 260 articulate3D"; do
  set -- $card
  # The donut's centre % is the repo's top language share; name it under the donut.
  lang=$(gh api "repos/ManveerAnand/$4" --jq '.language // ""')
  x=$(($2 + 6 + 348)); y=$(($3 + 6 + 135))
  label="<style>.lbl{animation:lf .6s ease-out 1.2s both}@keyframes lf{from{opacity:0}}@media (prefers-reduced-motion:reduce){.lbl{animation:none}}</style><text class=\"lbl\" x=\"$x\" y=\"$y\" text-anchor=\"middle\" font-family=\"ui-monospace,Consolas,monospace\" fill=\"#a5b4fc\"><tspan font-size=\"10\" font-weight=\"700\">$lang</tspan><tspan x=\"$x\" dy=\"11\" font-size=\"8\" fill-opacity=\".7\">top language</tspan></text>"
  sed -e "s#$root#width=\"406\" height=\"174\" viewBox=\"$2 $3 406 174\"#" \
      -e "s|</svg>|$label</svg>|" "$out/projects.svg" > "$out/card-$1.svg"
done

