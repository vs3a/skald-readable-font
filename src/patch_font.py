#!/usr/bin/env python3
"""
SKALD: Against the Black Priory - Readable Font Mod (04b_03)

Redraws the small UI text font (the TinyFont* bitmap atlases inside resources.assets) with 04b_03.
It works on the file's structure, not on a fixed checksum, so it is not tied to one game version.
If the atlases do not look like the expected layout, it refuses and changes nothing.

    SKALD-Font-Patcher.exe                      interactive menu
    SKALD-Font-Patcher.exe --apply              apply   (finds the game, or use --game "<folder>")
    SKALD-Font-Patcher.exe --restore            undo
    python patch_font.py --apply                same thing from source (needs: pip install UnityPy)
"""
import argparse, collections, glob, hashlib, json, os, shutil, subprocess, sys, time

VERSION = "1.1.0"
CELL, COLS, ROWS = 8, 9, 10
ORIG_SIZE = (71, 79)                                   # 9x10 cells of 7x7 + 1px separators
NEW_SIZE = (COLS * CELL + COLS - 1, ROWS * CELL + ROWS - 1)
SEP = (255, 0, 255, 255)
WHITE = (255, 255, 255, 255)
SPLIT = 3                                              # cell rows <= SPLIT: upper colour, below: white (as the original)
LAYOUT = ["#<>;{}|\u21b3 ", "'\"()=*_[]", "9.,:/%-+?", "012345678", "stuvwxyz!",
          "jklmnopqr", "abcdefghi", "STUVWXYZ ", "JKLMNOPQR", "ABCDEFGHI"]
TARGETS = {"TinyFont": "normal", "TinyFontYellow": "normal", "TinyFontTall": "normal",
           "TinyFontCapitalized": "caps", "TinyFontCapitalizedYellow": "caps",
           "TinyFontTallCapitalized": "caps", "TinyFontFat": "fat"}
DATA_DIRS = ("SKALD Against the Black Priory_Data",)


def resource(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def say(msg=""):
    print(msg, flush=True)


def die(msg):
    say("\nERROR: " + msg)
    say("Nothing was changed.")
    sys.exit(1)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


# ----------------------------------------------------------------------------- locating the game
def find_assets(root):
    """resources.assets inside a game folder (Windows, Linux or macOS layouts), searched a few levels deep"""
    if os.path.isfile(root) and os.path.basename(root).lower() == "resources.assets":
        return root
    found = []
    root = os.path.abspath(root)
    for cur, dirs, files in os.walk(root):
        if cur[len(root):].count(os.sep) >= 4:
            dirs[:] = []
            continue
        if "resources.assets" in files:
            found.append(os.path.join(cur, "resources.assets"))
    found.sort(key=lambda p: (not any(k in p.lower() for k in ("skald", "_data")), len(p)))
    return found[0] if found else None


def auto_find_game():
    here = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
    roots = [os.getcwd(), here, os.path.dirname(here)]
    for drive in ("C", "D", "E", "F", "G"):
        for p in (r"GOG Games\SKALD - Against the Black Priory", r"GOG Games\SKALD Against the Black Priory",
                  r"Program Files (x86)\GOG Galaxy\Games\SKALD - Against the Black Priory",
                  r"Program Files (x86)\Steam\steamapps\common\SKALD Against the Black Priory",
                  r"SteamLibrary\steamapps\common\SKALD Against the Black Priory",
                  r"Games\SKALD Against the Black Priory", r"GAMES\SKALD Against the Black Priory"):
            roots.append("%s:\\%s" % (drive, p))
    for r in roots:
        if os.path.isdir(r):
            for d in DATA_DIRS:
                cand = os.path.join(r, d, "resources.assets")
                if os.path.isfile(cand):
                    return cand
    return None


def game_running():
    if os.name != "nt":
        return False
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq SKALD Against the Black Priory.exe"],
                             capture_output=True, text=True, timeout=15).stdout
        return "SKALD Against the Black Priory.exe" in out
    except Exception:
        return False


# ----------------------------------------------------------------------------- reading / building atlases
def load_env(path):
    """loads from memory so no file handle stays open (Windows would refuse to rename the file otherwise)"""
    try:                                   # UnityPy imports an audio library we never use;
        import fmod_toolkit                # if it is missing or cannot load, a stub is enough
    except Exception:
        import types
        sys.modules["fmod_toolkit"] = types.ModuleType("fmod_toolkit")
    import UnityPy
    with open(path, "rb") as f:
        return UnityPy.load(f.read())


def tiny_textures(env):
    found = {}
    for o in env.objects:
        if o.type.name == "Texture2D":
            d = o.read()
            if d.m_Name in TARGETS:
                found[d.m_Name] = (o, d)
    return found


def state_of(env):
    """'original' | 'patched' | None, judged from the TinyFont atlas size"""
    t = tiny_textures(env)
    if "TinyFont" not in t:
        return None
    size = (t["TinyFont"][1].m_Width, t["TinyFont"][1].m_Height)
    return "original" if size == ORIG_SIZE else "patched" if size == NEW_SIZE else None


GLYPHS = None


def glyph_pixels(ch, mode):
    global GLYPHS
    if GLYPHS is None:
        with open(resource("glyphs_04b.json"), encoding="utf-8") as f:
            GLYPHS = json.load(f)
    rows = GLYPHS[ch.upper() if mode == "caps" else ch]
    return {(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c == "#"}


def colours(img):
    """upper / lower colour of the original glyphs: upper rows grey / yellow / black, lower rows white"""
    c = collections.Counter(p for p in img.getdata()
                            if p[3] > 0 and p != SEP and not (p[0] > 200 and p[2] > 200 and p[1] < 80))
    non_white = [k for k, _ in c.most_common() if k[:3] != (255, 255, 255)]
    upper = (non_white[0][:3] + (255,)) if non_white else WHITE
    return upper, (WHITE if WHITE in c else upper)


def build_atlas(old, mode):
    from PIL import Image
    upper, lower = colours(old)
    W, H = NEW_SIZE
    new = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = new.load()
    for y in range(H):
        if y % (CELL + 1) == CELL:
            for x in range(W):
                px[x, y] = SEP
    for x in range(W):
        if x % (CELL + 1) == CELL:
            for y in range(H):
                px[x, y] = SEP
    for r, row in enumerate(LAYOUT):
        for c, ch in enumerate(row):
            if ch in " \u21b3":
                continue
            pts = glyph_pixels(ch, mode)
            if mode == "fat":
                grown = set(pts)
                for x, y in pts:
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        grown.add((x + dx, y + dy))
                pts = grown
            ox, oy = c * (CELL + 1), r * (CELL + 1)
            for x, y in pts:
                if 0 <= x < CELL and 0 <= y < CELL:
                    px[ox + x, oy + y] = upper if (y <= SPLIT or mode == "fat") else lower
    return new


def make_patched(src, dst):
    say("Reading game data (a few seconds)...")
    env = load_env(src)
    tex = tiny_textures(env)
    if "TinyFont" not in tex:
        die("This game version has no 'TinyFont' atlas - not supported.")
    patched = []
    for name, (o, d) in tex.items():
        if (d.m_Width, d.m_Height) != ORIG_SIZE:
            say("  skipping %s (unexpected size %dx%d)" % (name, d.m_Width, d.m_Height))
            continue
        d.image = build_atlas(d.image.convert("RGBA"), TARGETS[name])
        d.save()
        patched.append(name)
    if "TinyFont" not in patched:
        die("The TinyFont atlas has an unexpected layout - this game version is not supported.")
    say("  redrew: " + ", ".join(sorted(patched)))
    say("Writing new file...")
    with open(dst, "wb") as f:
        f.write(env.file.save())
    chk = load_env(dst)
    if state_of(chk) != "patched" or len(list(chk.objects)) != len(list(env.objects)):
        os.remove(dst)
        die("Verification of the new file failed.")


# ----------------------------------------------------------------------------- actions
def paths(assets):
    return assets + ".original", assets + ".original.json"


def do_apply(assets):
    bak, manifest = paths(assets)
    size = os.path.getsize(assets)
    if shutil.disk_usage(os.path.dirname(assets)).free < size * 3:
        die("Not enough free disk space (need about 3x the size of resources.assets, ~600 MB).")
    say("Checking current file...")
    env = load_env(assets)
    st = state_of(env)
    del env
    if st is None:
        die("resources.assets does not look like a supported SKALD build (TinyFont atlas not found / unexpected layout).")
    if st == "original":
        say("Creating backup: " + os.path.basename(bak) + " (~%d MB)" % (size >> 20))
        shutil.copyfile(assets, bak)
        src = bak
        orig_hash = sha256(bak)
    else:   # already patched by us: rebuild from the backup
        meta = json.load(open(manifest)) if os.path.isfile(manifest) else None
        if not (os.path.isfile(bak) and meta and meta.get("patched_sha256") == sha256(assets)):
            die("The game is already modified, and no matching backup was found. "
                "Use the store's 'Verify / Repair', then run this again.")
        src, orig_hash = bak, meta["original_sha256"]
    tmp = assets + ".new"
    try:
        make_patched(src, tmp)
        os.replace(tmp, assets)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    with open(manifest, "w") as f:
        json.dump({"tool": VERSION, "original_sha256": orig_hash, "patched_sha256": sha256(assets)}, f)
    say("\nDone! Start the game. To undo, run this again and choose Restore.")


def do_restore(assets, force=False):
    bak, manifest = paths(assets)
    if not (os.path.isfile(bak) and os.path.isfile(manifest)):
        die("No backup found - nothing to restore. (Use the store's 'Verify / Repair' if needed.)")
    meta = json.load(open(manifest))
    if sha256(assets) != meta.get("patched_sha256") and not force:
        die("resources.assets has changed since the mod was applied (game update?). Restoring the old backup would "
            "downgrade it. Use the store's 'Verify / Repair' instead, or add --force.")
    shutil.copyfile(bak, assets)
    if sha256(assets) != meta["original_sha256"]:
        die("Restore verification failed. Use the store's 'Verify / Repair'.")
    say("Done. Original font restored.")


def main():
    ap = argparse.ArgumentParser(description="SKALD readable font (04b_03) patcher")
    ap.add_argument("--game", help="game folder (or the resources.assets file)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true")
    g.add_argument("--restore", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    interactive = not (a.apply or a.restore)

    say("SKALD Readable Font Mod %s" % VERSION)
    say("-" * 30)
    assets = find_assets(a.game) if a.game else auto_find_game()
    if not assets and interactive:
        p = input("Game folder not found. Paste its path (the folder with the game .exe): ").strip().strip('"')
        assets = find_assets(p) if p else None
    if not assets:
        die("Could not find resources.assets. Use --game \"<game folder>\".")
    say("Using: " + assets)
    if game_running():
        die("The game is running. Close it first.")
    try:
        if interactive:
            say("\n  [1] Apply the 04b_03 font\n  [R] Restore the original font\n  [Q] Quit")
            c = input("Your choice: ").strip().lower()
            if c == "1":
                do_apply(assets)
            elif c == "r":
                do_restore(assets, a.force)
        elif a.apply:
            do_apply(assets)
        else:
            do_restore(assets, a.force)
    except PermissionError as e:
        die("Permission denied (%s). Close the game / launcher, or run from a folder you can write to." % e)
    if interactive:
        input("\nPress Enter to close...")


if __name__ == "__main__":
    main()
