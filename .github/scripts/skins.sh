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

# Tech stack: one image per tool so each can link to the repo that uses it.
# A one-logo strip is 420x100 with the tile at (8,8) 104x76; crop to just the tile.
# Every first tile gets the same yellow border, so recolour each from the README palette.
palette=(fcca1b 779dff 5eead4 c084fc 8ed345 ff7a90 5eead4 ff7a90 c084fc)
i=0
for logo in Python TypeScript C C++ Go Bash Node.js Git GitHub; do
  name="tile-$(echo "$logo" | tr 'A-Z' 'a-z' | sed 's/+/p/g; s/\./-/g')"
  fetch "$name" "https://www.gitskins.com/api/readme-reference/technology-stack?username=manveeranand&theme=midnight&logos=$(printf %s "$logo" | sed 's/+/%2B/g')"
  grep -q 'viewBox="0 0 420 100"' "$out/$name.svg" || { echo "$name.svg layout changed" >&2; exit 1; }
  sed -i -e 's#width="420" height="100" viewBox="0 0 420 100"#width="108" height="80" viewBox="6 6 108 80"#' \
         -e "s#stroke=\"\#f7df1e\"#stroke=\"\#${palette[$i]}\"#" "$out/$name.svg"
  i=$((i + 1))
done
