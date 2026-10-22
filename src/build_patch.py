"""
Rebuilds the patched resources.assets (developers only - players just run Patch-Font.bat).

    py -3.10 -m pip install UnityPy Pillow
    py -3.10 build_patch.py <original resources.assets> <output> <path to 04B_03__.TTF>

Then make the patch with xdelta3 (run it from a short path: xdelta3 cannot open paths over 260 characters):
    xdelta3 -f -B 268435456 -e -s <original> <output> 04b_03.xdelta

How it works
  * The small UI text of SKALD is drawn from bitmap atlases (TinyFont*). Each atlas is a 9x10 grid of square cells
    separated by 1px magenta lines; the game slices cells by those lines, so cells may be larger than the original 7x7
    as long as they stay square.
  * Every glyph is redrawn in the same grid position with 04b_03 at 8 px, keeping the original two-tone shading
    (upper rows base colour, lower rows white). The "Fat" (outline) atlas is rebuilt by dilating the new glyphs.
  * wordHeight of the Tiny* font entries in the embedded SkaldProject json stays 7, so UI layout does not shift.
"""
import collections, re, sys
import UnityPy
from PIL import Image, ImageDraw, ImageFont

if len(sys.argv) != 4:
    sys.exit(__doc__)
SRC, OUT, TTF = sys.argv[1:4]
COLS, ROWS = 9, 10
MAGENTA = (255, 0, 255, 255)
WHITE = (255, 255, 255, 255)
CW = CH = 8              # square cell: 1 blank column/row + 7x7 glyph box
ORIGX, BASE = 1, 6       # glyph origin column and baseline row inside a cell
SPLIT = 3                # cell rows <= SPLIT use the upper colour, the rest white (like the original)

LAYOUT = ["#<>;{}|↳ ", "'\"()=*_[]", "9.,:/%-+?", "012345678", "stuvwxyz!",
          "jklmnopqr", "abcdefghi", "STUVWXYZ ", "JKLMNOPQR", "ABCDEFGHI"]
TARGETS = {"TinyFont": "normal", "TinyFontYellow": "normal", "TinyFontTall": "normal",
           "TinyFontCapitalized": "caps", "TinyFontCapitalizedYellow": "caps",
           "TinyFontTallCapitalized": "caps", "TinyFontFat": "fat"}
font = ImageFont.truetype(TTF, 8)

def glyph_pixels(ch, mode):
    im = Image.new("L", (CW, CH), 0)
    d = ImageDraw.Draw(im); d.fontmode = "1"
    d.text((ORIGX, BASE), ch.upper() if mode == "caps" else ch, font=font, fill=255, anchor="ls")
    p = im.load()
    return {(x, y) for y in range(CH) for x in range(CW) if p[x, y]}

def colours(img):
    c = collections.Counter(p for p in img.getdata() if p[3] > 0 and p != MAGENTA and not (p[0] > 200 and p[2] > 200 and p[1] < 80))
    non_white = [k for k, _ in c.most_common() if k[:3] != (255, 255, 255)]
    upper = (non_white[0][:3] + (255,)) if non_white else WHITE
    return upper, (WHITE if WHITE in c else upper)

def build_atlas(old, mode):
    upper, lower = colours(old)
    W = COLS * CW + (COLS - 1); H = ROWS * CH + (ROWS - 1)
    new = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = new.load()
    for y in range(H):
        if y % (CH + 1) == CH:
            for x in range(W): px[x, y] = MAGENTA
    for x in range(W):
        if x % (CW + 1) == CW:
            for y in range(H): px[x, y] = MAGENTA
    for r, row in enumerate(LAYOUT):
        for c, ch in enumerate(row):
            if ch in " ↳":
                continue
            pts = glyph_pixels(ch, mode)
            if mode == "fat":
                grown = set(pts)
                for x, y in pts:
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        grown.add((x + dx, y + dy))
                pts = grown
            ox, oy = c * (CW + 1), r * (CH + 1)
            for x, y in pts:
                if 0 <= x < CW and 0 <= y < CH:
                    px[ox + x, oy + y] = upper if (y <= SPLIT or mode == "fat") else lower
    return new

env = UnityPy.load(SRC)
done = []
for o in env.objects:
    if o.type.name == "Texture2D":
        d = o.read()
        if d.m_Name in TARGETS:
            old = d.image.convert("RGBA")
            assert old.size == (71, 79), (d.m_Name, old.size)
            d.image = build_atlas(old, TARGETS[d.m_Name])
            d.save()
            done.append(d.m_Name)
print("textures:", sorted(done))
for o in env.objects:
    if o.type.name == "TextAsset":
        d = o.read()
        if d.m_Name == "SkaldProject":
            pat = re.compile(r'("wordHeight": )7(,\s*"title": "",\s*"description": "",\s*"imagePath": "",\s*"modelPath": "Tiny)')
            s2, n = pat.subn(r"\g<1>7\2", d.m_Script)
            print("wordHeight entries:", n)
            d.m_Script = s2
            d.save()
open(OUT, "wb").write(env.file.save())
print("saved", OUT)
