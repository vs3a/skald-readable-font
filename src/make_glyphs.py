"""
Developer tool: renders 04b_03 at 8 px into glyphs_04b.json (one 8x8 pixel mask per character).
patch_font.py only needs that json, not the font file.

    py -3 -m pip install Pillow
    py -3 make_glyphs.py path\to\04B_03__.TTF
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

if len(sys.argv) != 2:
    sys.exit(__doc__)
CELL, ORIGX, BASE = 8, 1, 6          # 8x8 cell, 1 blank column on the left, baseline on row 6
font = ImageFont.truetype(sys.argv[1], 8)
chars = "#<>;{}|'\"()=*_[]9.,:/%-+?0123456789!" + "abcdefghijklmnopqrstuvwxyz" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
out = {}
for ch in chars:
    im = Image.new("L", (CELL, CELL), 0)
    d = ImageDraw.Draw(im); d.fontmode = "1"
    d.text((ORIGX, BASE), ch, font=font, fill=255, anchor="ls")
    p = im.load()
    out[ch] = ["".join("#" if p[x, y] else "." for x in range(CELL)) for y in range(CELL)]
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glyphs_04b.json")
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=0)
print("wrote", path, len(out), "glyphs")
