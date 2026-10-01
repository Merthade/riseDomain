#!/usr/bin/env python3
"""Frame Rise 1.33 captures in an iPhone shell for the site (shell copied from
AlarmPlanner website/_gen/frame_web.py). Raws: Marketing/screenshots/raw (store set,
2026-09-26) and fresh captures from `--fixture=shots` (DebugLaunch.swift). Needs Pillow.

    python3 _gen/frame_web.py <dir with fresh home/wake/timer/complete/winddown.png>
"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "assets")
STORE_RAW = os.path.join(os.path.dirname(HERE), "Marketing/screenshots/raw")
FRESH = sys.argv[1] if len(sys.argv) > 1 else STORE_RAW
FINAL = (600, 1203)

# Same ratios as Images/frame_shot.py
SCREEN_R_RATIO = 0.145
BEZEL_RATIO    = 0.030
RIM_RATIO      = 0.011
RIM_COLOR      = (0x2C, 0x2C, 0x2D, 255)


def shell_with_buttons(img):
    """frame_shot.py's shell, on a canvas wide enough for the buttons to show."""
    img = img.convert("RGBA")
    sw, height = img.size

    scr_r = int(sw * SCREEN_R_RATIO)
    bez   = max(6, int(sw * BEZEL_RATIO))
    rimw  = max(2, int(sw * RIM_RATIO))
    bwid  = max(3, rimw * 2)

    fw, fh = sw + (bez + rimw) * 2, height + (bez + rimw) * 2
    W, H = fw + bwid * 2, fh
    ox = bwid
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)

    unit = fh / 100
    for y0, y1 in [(20, 26), (30, 40), (42, 52)]:               # action, vol up, vol down
        d.rounded_rectangle([2, int(unit * y0), ox + 2, int(unit * y1)],
                            radius=bwid // 2, fill=RIM_COLOR)
    d.rounded_rectangle([ox + fw - 2, int(unit * 33), W - 2, int(unit * 50)],  # power
                        radius=bwid // 2, fill=RIM_COLOR)

    d.rounded_rectangle([(ox, 0), (ox + fw - 1, fh - 1)], radius=scr_r + bez + rimw, fill=RIM_COLOR)
    d.rounded_rectangle([(ox + rimw, rimw), (ox + fw - rimw - 1, fh - rimw - 1)],
                        radius=scr_r + bez, fill=(8, 8, 10, 255))

    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([(0, 0), img.size], radius=scr_r, fill=255)
    img.putalpha(m)
    out.paste(img, (ox + bez + rimw, bez + rimw), img)
    return out



def add_dynamic_island(img):
    """Simulator captures have no Dynamic Island; draw it. iPhone 17 Pro Max geometry:
    ~125x37 pt, 11 pt from the top, at 3x on a 1320 px (440 pt) wide capture."""
    w, h = img.size
    k = w / 440
    iw, ih, top = 125 * k, 37 * k, 11 * k
    x0 = (w - iw) / 2
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, top, x0 + iw, top + ih], radius=ih / 2, fill=(0, 0, 0, 255))
    # Front camera: a ~12 pt lens near the island's right end, a dark ring with a faint
    # blue-violet core and a tiny highlight, so it reads at thumbnail size.
    cx, cy, r = x0 + iw - 18.5 * k, top + ih / 2, 6 * k
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(18, 18, 26, 255))
    r2 = r * 0.62
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(10, 12, 30, 255))
    r3 = r * 0.30
    d.ellipse([cx - r3, cy - r3, cx + r3, cy + r3], fill=(28, 34, 72, 255))
    h = r * 0.16
    d.ellipse([cx - r * 0.35 - h, cy - r * 0.35 - h, cx - r * 0.35 + h, cy - r * 0.35 + h], fill=(70, 80, 120, 255))
    return img


JOBS = {
    "shot-home.webp":      f"{FRESH}/home.png",
    "shot-wake.webp":      f"{FRESH}/wake.png",
    "shot-timer.webp":     f"{FRESH}/timer.png",
    "shot-complete.webp":  f"{FRESH}/complete.png",
    "shot-winddown.webp":  f"{FRESH}/winddown.png",
    # The fixture's streak calendar is empty on the 1st of a month; the 09-26 store raw is full.
    "shot-streak.webp":    f"{STORE_RAW}/streak_en.png",
    "shot-ringing.webp":   f"{STORE_RAW}/wakealert_en.png",
}

if __name__ == "__main__":
    for name, path in JOBS.items():
        img = add_dynamic_island(Image.open(path).convert("RGBA"))
        framed = shell_with_buttons(img).resize(FINAL, Image.LANCZOS)
        dst = os.path.join(OUT, name)
        framed.save(dst, "WEBP", quality=82, method=6)
        print(f"{name}  {os.path.getsize(dst)//1024}KB")
