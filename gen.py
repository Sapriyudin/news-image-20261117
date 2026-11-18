#!/usr/bin/env python3
"""Render news-image-20261117 variants. Local build only (uses PIL + DejaVu).
Deterministic: no time, no randomness, fixed layout. Usage: python3 gen.py A|B|C
Writes candidates/<variant>/entry.png (1024x1024)."""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from stories import STORIES, NUMBERS, TIMELINE

W = H = 1024
M = 28
CW = W - 2 * M  # 968 content width
PAPER = (246, 241, 227)
INK = (22, 21, 19)
RED = (163, 22, 33)
MUTED = (110, 103, 89)
LINE = (201, 191, 166)
SEA = (220, 231, 229)
LAND = (239, 231, 206)
LAND_LINE = (154, 143, 118)
SKY = (191, 211, 222)
WATER = (127, 168, 201)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def F(path, size):
    return ImageFont.truetype(path, size)


def wrap(d, text, font, maxw):
    """Greedy word wrap; returns list of lines that fit maxw."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=font) <= maxw:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(d, x, y, lines, font, fill=INK, leading=None):
    """Draw lines; returns y after the last line."""
    lh = leading or int(font.size * 1.22)
    for ln in lines:
        d.text((x, y), ln, font=font, fill=fill)
        y += lh
    return y


def fit_lines(d, text, font, maxw, max_lines):
    """Wrap, shrinking font until it fits max_lines (min 11px)."""
    size = font.size
    while size > 11:
        f = ImageFont.truetype(font.path, size) if hasattr(font, "path") else font
        lines = wrap(d, text, f, maxw)
        if len(lines) <= max_lines:
            return f, lines
        size -= 1
    f = ImageFont.truetype(font.path, 11) if hasattr(font, "path") else font
    return f, wrap(d, text, f, maxw)[:max_lines]


def num_badge(d, x, y, n, r=11):
    d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=RED)
    f = F(SANS_B, 13 if r >= 11 else 10)
    t = str(n)
    tw = d.textlength(t, font=f)
    d.text((x + r - tw / 2, y + r - 7 if r >= 11 else y + r - 5), t, font=f, fill=(255, 255, 255))


def section_label(d, x, y, text):
    f = F(SANS_B, 13)
    d.text((x, y), text, font=f, fill=RED)
    d.line([(x, y + 20), (x + CW, y + 20)], fill=RED, width=2)
    return y + 28


# ---------------------------------------------------------------- icons
# ---------------------------------------------------------------- icons
def draw_icon(d, s, x, y, w, h):
    """Original flat editorial illustration inside box (x,y,w,h), drawn for
    the story dict s. Richer mini-scenes: sky, sun, clouds, smoke, debris,
    skylines, scoreboards — all drawn from scratch with PIL primitives."""
    kind = s["icon"]
    sky_h = int(h * 0.62)
    if kind in ("bridge", "drone", "jet", "plane", "tanker"):
        d.rectangle([x, y, x + w, y + sky_h], fill=SKY)
        d.rectangle([x, y + sky_h, x + w, y + h], fill=WATER)
        stipple(d, x, y, w, sky_h, (168, 192, 205), n=110, seed=x + y)
        stipple(d, x, y + sky_h, w, h - sky_h, (110, 150, 185), n=60, seed=x * 3 + y)
    elif kind in ("football", "leaf", "frog", "panda", "dino"):
        d.rectangle([x, y, x + w, y + h], fill=(226, 232, 214))
    elif kind in ("chart_down", "chart_up"):
        d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
    elif kind in ("chip", "robot", "lab", "deal"):
        d.rectangle([x, y, x + w, y + h], fill=(228, 230, 236))
    else:
        d.rectangle([x, y, x + w, y + h], fill=(238, 232, 216))
    cx, cy = x + w / 2, y + h / 2
    if kind == "bridge":
        # sun + clouds
        d.ellipse([x + w - 34, y + 8, x + w - 14, y + 28], fill=(245, 220, 130))
        for cx0 in (x + 16, x + int(w * 0.45)):
            d.ellipse([cx0, y + 12, cx0 + 34, y + 22], fill=(250, 250, 245))
        deck = y + sky_h - 8
        # two towers with cross-bracing
        for tx in (x + w * 0.18, x + w * 0.72):
            d.rectangle([tx, y + 26, tx + 6, deck], fill=(60, 58, 54))
            d.rectangle([tx - 6, y + 22, tx + 12, y + 28], fill=(60, 58, 54))
            d.rectangle([tx, y + 44, tx + 6, y + 48], fill=(60, 58, 54))
        # deck standing left and right, gap in the middle
        d.rectangle([x + 4, deck, x + w * 0.40, deck + 6], fill=(60, 58, 54))
        d.rectangle([x + w * 0.60, deck, x + w - 4, deck + 6], fill=(60, 58, 54))
        # fallen span: tilted slab sinking into the water
        d.polygon([(x + w * 0.42, deck + 2), (x + w * 0.56, deck + 2),
                   (x + w * 0.52, deck + 26), (x + w * 0.46, deck + 26)], fill=(90, 86, 80))
        # smoke plumes rising from the gap
        for sx, sy, sr in ((x + w * 0.47, y + 16, 9), (x + w * 0.52, y + 8, 7),
                           (x + w * 0.44, y + 26, 6)):
            d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(200, 196, 188))
        # debris in the water
        for dx, dy in ((x + w * 0.46, deck + 34), (x + w * 0.55, deck + 40)):
            d.rectangle([dx, dy, dx + 12, dy + 4], fill=(90, 86, 80))
        # small red boat
        bx0 = x + w * 0.68
        d.polygon([(bx0, deck + 14), (bx0 + 26, deck + 14), (bx0 + 20, deck + 22),
                   (bx0 + 6, deck + 22)], fill=(163, 22, 33))
        d.line([(bx0 + 12, deck + 14), (bx0 + 12, deck + 2)], fill=(60, 58, 54), width=2)
        # second boat farther away, and birds over the strait
        bx1 = x + w * 0.12
        d.polygon([(bx1, deck + 20), (bx1 + 18, deck + 20), (bx1 + 14, deck + 26),
                   (bx1 + 4, deck + 26)], fill=(90, 86, 80))
        for bxx, byy in ((x + w * 0.30, y + 34), (x + w * 0.36, y + 28), (x + w * 0.60, y + 36)):
            d.line([(bxx - 5, byy), (bxx, byy - 4), (bxx + 5, byy)], fill=(60, 58, 54), width=2)
        for wx in range(0, int(w), 26):
            d.arc([x + wx, y + sky_h + 12, x + wx + 18, y + sky_h + 22], 0, 180,
                  fill=(255, 255, 255), width=2)
    elif kind == "drone":
        # sun + base buildings
        d.ellipse([x + 10, y + 8, x + 28, y + 26], fill=(245, 220, 130))
        for i, bh in enumerate((16, 24, 14)):
            bx0 = x + 12 + i * 30
            d.rectangle([bx0, y + h - 6 - bh, bx0 + 22, y + h - 6], fill=(90, 86, 80))
        d.line([(x + 6, y + h * 0.55), (x + w - 6, y + h * 0.30)], fill=(90, 86, 80), width=2)
        bx, by = cx - 12, cy - 8
        d.rectangle([bx, by, bx + 24, by + 12], fill=(40, 40, 44))
        for ox, oy in ((bx - 8, by - 6), (bx + 24, by - 6), (bx - 8, by + 8), (bx + 24, by + 8)):
            d.line([(ox - 6, oy), (ox + 10, oy)], fill=(40, 40, 44), width=3)
        d.ellipse([cx - 3, by + 12, cx + 3, by + 18], fill=RED)
        # explosion burst near the base
        ex, ey = x + w * 0.80, y + h * 0.70
        pts = []
        for k in range(16):
            ang = math.pi * k / 8
            r = 14 if k % 2 == 0 else 6
            pts.append((ex + r * math.cos(ang), ey + r * math.sin(ang)))
        d.polygon(pts, fill=(230, 120, 30))
        d.ellipse([ex - 5, ey - 5, ex + 5, ey + 5], fill=(245, 200, 60))
    elif kind == "jet":
        d.ellipse([x + w - 30, y + 8, x + w - 12, y + 26], fill=(245, 220, 130))
        d.polygon([(x + w * 0.15, cy), (x + w * 0.55, cy - 12), (x + w * 0.92, cy - 4),
                   (x + w * 0.92, cy + 4), (x + w * 0.55, cy + 12)], fill=(70, 72, 78))
        d.polygon([(x + w * 0.45, cy - 10), (x + w * 0.62, cy - 30), (x + w * 0.66, cy - 8)], fill=(70, 72, 78))
        d.line([(x + 4, cy + 14), (x + w * 0.45, cy + 6)], fill=(255, 255, 255), width=2)
        d.line([(x + 4, cy + 22), (x + w * 0.40, cy + 12)], fill=(255, 255, 255), width=2)
    elif kind == "plane":
        d.ellipse([x + w - 30, y + 8, x + w - 12, y + 26], fill=(245, 220, 130))
        for cx0, cy0 in ((x + 12, y + 12), (x + int(w * 0.52), y + 6)):
            d.ellipse([cx0, cy0, cx0 + 30, cy0 + 10], fill=(250, 250, 245))
        d.polygon([(x + w * 0.12, cy), (x + w * 0.85, cy - 8), (x + w * 0.95, cy),
                   (x + w * 0.85, cy + 8)], fill=(70, 72, 78))
        d.polygon([(x + w * 0.42, cy - 6), (x + w * 0.58, cy - 26), (x + w * 0.64, cy - 4)], fill=(70, 72, 78))
        d.polygon([(x + w * 0.42, cy + 6), (x + w * 0.58, cy + 24), (x + w * 0.64, cy + 4)], fill=(70, 72, 78))
        d.line([(x + 4, cy + 12), (x + w * 0.5, cy + 4)], fill=(255, 255, 255), width=2)
        d.line([(x + 4, cy + 20), (x + w * 0.45, cy + 12)], fill=(255, 255, 255), width=2)
    elif kind == "summit":
        # skyline behind the flags
        for i, bh in enumerate((18, 30, 24, 36, 22)):
            bx0 = x + 10 + i * (w - 20) / 5
            d.rectangle([bx0, y + h - 12 - bh, bx0 + (w - 20) / 5 - 4, y + h - 12],
                        fill=(120, 118, 112))
        for i, col in enumerate(((163, 22, 33), (30, 80, 140), (230, 130, 30), (40, 120, 70))):
            px = x + w * (0.16 + 0.23 * i)
            d.line([(px, y + 8), (px, y + h - 12)], fill=(60, 58, 54), width=3)
            d.polygon([(px, y + 8), (px + 26, y + 16), (px, y + 24)], fill=col)
        d.rectangle([x + 8, y + h - 12, x + w - 8, y + h - 8], fill=(60, 58, 54))
    elif kind == "chip":
        # faint circuit traces on the background
        for tx0, ty0, tx1, ty1 in ((x + 8, y + 10, x + w - 8, y + 10),
                                   (x + 8, y + h - 10, x + w - 8, y + h - 10),
                                   (x + 10, y + 8, x + 10, y + h - 8)):
            d.line([(tx0, ty0), (tx1, ty1)], fill=(190, 195, 205), width=2)
            d.ellipse([tx1 - 3, ty1 - 3, tx1 + 3, ty1 + 3], fill=(150, 160, 175))
        s = min(w, h) * 0.52
        bx, by = cx - s / 2, cy - s / 2
        d.rectangle([bx, by, bx + s, by + s], fill=(30, 34, 44))
        d.rectangle([bx + s * 0.28, by + s * 0.28, bx + s * 0.72, by + s * 0.72],
                    outline=(120, 180, 220), width=2)
        d.rectangle([bx + s * 0.42, by + s * 0.42, bx + s * 0.58, by + s * 0.58], fill=(163, 22, 33))
        for i in range(4):
            px = bx + s * (0.2 + 0.2 * i)
            d.line([(px, by - 8), (px, by)], fill=(30, 34, 44), width=3)
            d.line([(px, by + s), (px, by + s + 8)], fill=(30, 34, 44), width=3)
    elif kind in ("chart_down", "chart_up"):
        for gy in (y + h * 0.30, y + h * 0.55, y + h * 0.80):
            d.line([(x + 10, gy), (x + w - 6, gy)], fill=(232, 230, 224), width=1)
        d.line([(x + 10, y + 8), (x + 10, y + h - 10), (x + w - 6, y + h - 10)],
               fill=(60, 58, 54), width=2)
        vals = [0.85, 0.65, 0.45, 0.25] if kind == "chart_down" else [0.25, 0.45, 0.65, 0.85]
        bw = (w - 24) / 4
        col = RED if kind == "chart_down" else (40, 120, 70)
        for i, v in enumerate(vals):
            bh = (h - 26) * v
            d.rectangle([x + 14 + i * bw, y + h - 10 - bh, x + 14 + (i + 1) * bw - 4, y + h - 10], fill=col)
        # trend arrow across the bars
        ax0, ay0 = x + 14, y + (18 if kind == "chart_down" else h - 22)
        ax1, ay1 = x + w - 12, y + (h - 22 if kind == "chart_down" else 18)
        d.line([(ax0, ay0), (ax1, ay1)], fill=(30, 30, 34), width=2)
        d.polygon([(ax1, ay1), (ax1 - 10, ay1 - 2), (ax1 - 2, ay1 - 10)] if kind == "chart_down"
                  else [(ax1, ay1), (ax1 - 10, ay1 + 2), (ax1 - 2, ay1 + 10)], fill=(30, 30, 34))
    elif kind == "football":
        # mown stripes + goals + ball
        for i in range(4):
            d.rectangle([x + i * w / 4, y, x + (i + 1) * w / 4, y + h],
                        fill=(74, 140, 74) if i % 2 == 0 else (64, 128, 64))
        d.line([(x, cy), (x + w, cy)], fill=(255, 255, 255), width=2)
        d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], outline=(255, 255, 255), width=2)
        for gx in (x + 2, x + w - 8):
            d.rectangle([gx, cy - 14, gx + 6, cy + 14], outline=(255, 255, 255), width=2)
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(255, 255, 255))
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(40, 40, 40))
        if s.get("score"):
            d.rectangle([x, y, x + w, y + 16], fill=(30, 30, 34))
            tf = F(SANS_B, 11)
            t = "%s  %s  %s" % (s["teams"][0], s["score"], s["teams"][1])
            tw = d.textlength(t, font=tf)
            d.text((x + (w - tw) / 2, y + 2), t, font=tf, fill=(255, 255, 255))
            d.rectangle([x, y + h - 6, x + w, y + h], fill=s["kit"][0])
    elif kind == "virus":
        for bx0, by0, br in ((x + 14, y + 12, 5), (x + w - 18, y + 16, 4), (x + w - 14, y + h - 16, 6)):
            d.ellipse([bx0 - br, by0 - br, bx0 + br, by0 + br], fill=(220, 180, 200))
        r = min(w, h) * 0.26
        for a in range(0, 360, 45):
            ex = cx + (r + 8) * math.cos(math.radians(a))
            ey = cy + (r + 8) * math.sin(math.radians(a))
            d.line([(cx, cy), (ex, ey)], fill=(140, 40, 90), width=3)
            d.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=(140, 40, 90))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(140, 40, 90))
        d.ellipse([cx - r * 0.4, cy - r * 0.5, cx - r * 0.1, cy - r * 0.2], fill=(200, 120, 160))
    elif kind == "leaf":
        d.ellipse([x + 14, y + 10, x + 26, y + 22], fill=(200, 220, 180))
        d.ellipse([x + w - 26, y + 14, x + w - 14, y + 26], fill=(200, 220, 180))
        pts = [(cx, y + 6)]
        for i in range(1, 9):
            t = i / 8
            pts.append((cx + w * 0.30 * (1 - t * 0.55) * (1 - abs(t - 0.5)), y + 6 + (h - 18) * t))
        pts.append((cx, y + h - 8))
        for i in range(7, 0, -1):
            t = i / 8
            pts.append((cx - w * 0.30 * (1 - t * 0.55) * (1 - abs(t - 0.5)), y + 6 + (h - 18) * t))
        d.polygon(pts, fill=(60, 140, 70))
        d.line([(cx, y + 10), (cx, y + h - 10)], fill=(30, 90, 40), width=2)
    elif kind == "gavel":
        d.rectangle([cx - 22, cy - 16, cx + 22, cy - 2], fill=(120, 80, 40))
        d.rectangle([cx - 4, cy - 2, cx + 4, cy + 22], fill=(90, 60, 30))
        d.rectangle([x + 10, y + h - 14, x + w - 10, y + h - 10], fill=(120, 80, 40))
    elif kind == "tanker":
        d.rectangle([x + 8, cy - 6, x + w - 8, cy + 14], fill=(40, 40, 44))
        for i, col in enumerate(((163, 22, 33), (30, 80, 140), (40, 120, 70))):
            d.rectangle([x + 14 + i * 22, cy - 22, x + 30 + i * 22, cy - 6], fill=col)
        d.polygon([(cx + 18, cy - 34), (cx + 26, cy - 18), (cx + 10, cy - 18)], fill=(230, 120, 30))
        d.ellipse([cx + 14, cy - 38, cx + 22, cy - 30], fill=(230, 180, 40))
    elif kind == "flame":
        d.polygon([(cx, y + 8), (cx + 16, cy + 2), (cx + 12, cy + 14),
                   (cx + 22, cy + 8), (cx + 10, y + h - 10), (cx - 12, y + h - 10),
                   (cx - 20, cy + 6), (cx - 8, cy + 12)], fill=(230, 120, 30))
        d.ellipse([cx - 7, cy + 2, cx + 7, cy + 16], fill=(245, 200, 60))
    elif kind == "aid":
        # tent + stacked boxes + red-cross crate
        d.polygon([(cx - 34, y + h - 12), (cx, y + h - 42), (cx + 34, y + h - 12)], fill=(210, 190, 150))
        d.polygon([(cx - 9, y + h - 12), (cx, y + h - 30), (cx + 9, y + h - 12)], fill=(90, 70, 50))
        d.rectangle([x + w * 0.2, y + 8, x + w * 0.8, y + h * 0.52], fill=(255, 255, 255),
                    outline=(60, 58, 54), width=2)
        d.rectangle([cx - 5, y + 16, cx + 5, y + h * 0.46], fill=RED)
        d.rectangle([x + w * 0.28, cy - 14, x + w * 0.72, cy - 4], fill=RED)
    elif kind == "robot":
        d.rectangle([cx - 20, cy - 14, cx + 20, cy + 16], fill=(180, 185, 195),
                    outline=(60, 58, 54), width=2)
        d.line([(cx, cy - 14), (cx, cy - 26)], fill=(60, 58, 54), width=3)
        d.ellipse([cx - 4, cy - 30, cx + 4, cy - 22], fill=RED)
        d.ellipse([cx - 12, cy - 6, cx - 4, cy + 2], fill=(30, 34, 44))
        d.ellipse([cx + 4, cy - 6, cx + 12, cy + 2], fill=(30, 34, 44))
        d.line([(cx - 8, cy + 10), (cx + 8, cy + 10)], fill=(30, 34, 44), width=2)
    elif kind == "cart":
        d.polygon([(x + 12, y + 12), (x + w - 12, y + 12), (x + w - 20, cy + 8), (x + 18, cy + 8)],
                  outline=(60, 58, 54), width=3)
        d.line([(x + w - 12, y + 12), (x + w - 22, y + 4)], fill=(60, 58, 54), width=3)
        for wx in (cx - 12, cx + 10):
            d.ellipse([wx - 4, y + h - 14, wx + 4, y + h - 6], fill=(60, 58, 54))
    elif kind == "crowd":
        for i, px in enumerate((cx - 26, cx, cx + 26)):
            d.ellipse([px - 9, cy - 14, px + 9, cy + 4], fill=(200, 170, 140))
            d.pieslice([px - 16, cy + 2, px + 16, cy + 26], 180, 360,
                       fill=((70, 90, 140), (163, 22, 33), (40, 120, 70))[i])
    elif kind == "lab":
        d.polygon([(cx - 6, y + 10), (cx + 6, y + 10), (cx + 6, cy), (cx + 16, y + h - 12),
                   (cx - 16, y + h - 12), (cx - 6, cy)], outline=(60, 58, 54), width=3)
        d.polygon([(cx - 12, cy + 4), (cx + 12, cy + 4), (cx + 15, y + h - 13),
                   (cx - 15, y + h - 13)], fill=(80, 160, 200))
    elif kind == "frog":
        d.ellipse([cx - 26, cy - 6, cx + 26, cy + 18], fill=(90, 170, 80))
        for ex in (cx - 14, cx + 14):
            d.ellipse([ex - 9, cy - 18, ex + 9, cy - 2], fill=(90, 170, 80))
            d.ellipse([ex - 4, cy - 13, ex + 4, cy - 5], fill=(255, 255, 255))
            d.ellipse([ex - 2, cy - 11, ex + 2, cy - 7], fill=(20, 20, 20))
        d.arc([cx - 12, cy - 2, cx + 12, cy + 12], 0, 180, fill=(20, 20, 20), width=2)
    elif kind == "panda":
        d.ellipse([cx - 22, cy - 16, cx - 8, cy - 2], fill=(30, 30, 30))
        d.ellipse([cx + 8, cy - 16, cx + 22, cy - 2], fill=(30, 30, 30))
        d.ellipse([cx - 24, cy - 12, cx + 24, cy + 18], fill=(255, 255, 255),
                  outline=(200, 200, 200), width=1)
        for ex in (cx - 11, cx + 11):
            d.ellipse([ex - 6, cy - 6, ex + 6, cy + 6], fill=(30, 30, 30))
            d.ellipse([ex - 2, cy - 3, ex + 2, cy + 1], fill=(255, 255, 255))
        d.ellipse([cx - 3, cy + 4, cx + 3, cy + 9], fill=(30, 30, 30))
    elif kind == "dino":
        d.polygon([(x + 8, y + h - 12), (x + w * 0.30, y + h - 30), (x + w * 0.34, y + 14),
                   (x + w * 0.44, y + 10), (x + w * 0.42, y + h - 26), (x + w * 0.62, y + h - 26),
                   (x + w * 0.66, y + h - 12), (x + w * 0.55, y + h - 12), (x + w * 0.55, y + h - 22),
                   (x + w * 0.42, y + h - 22), (x + w * 0.42, y + h - 12),
                   (x + w * 0.80, y + h - 26), (x + w * 0.95, y + h - 34), (x + w * 0.92, y + h - 22),
                   (x + w * 0.70, y + h - 12)], fill=(110, 140, 90))
        d.ellipse([x + w * 0.34, y + 6, x + w * 0.46, y + 18], fill=(110, 140, 90))
    elif kind == "deal":
        d.ellipse([cx - 24, cy - 10, cx + 2, cy + 16], outline=(30, 80, 140), width=4)
        d.ellipse([cx - 2, cy - 10, cx + 24, cy + 16], outline=RED, width=4)


# ---------------------------------------------------------------- world map
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-80, 73), (-65, 60),
     (-55, 47), (-70, 42), (-75, 35), (-80, 25), (-90, 20), (-97, 16), (-105, 20),
     (-115, 30), (-125, 40), (-140, 60), (-155, 58), (-168, 66)],
    [(-55, 60), (-40, 70), (-30, 76), (-20, 70), (-30, 60), (-45, 60)],
    [(-80, 10), (-60, 5), (-50, 0), (-40, -10), (-35, -20), (-45, -30), (-55, -35),
     (-65, -45), (-70, -55), (-75, -40), (-80, -20), (-80, -5), (-80, 10)],
    [(-17, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (30, 31), (35, 28), (43, 12),
     (51, 11), (48, 0), (40, -10), (35, -20), (30, -30), (20, -35), (15, -25),
     (12, -5), (9, 4), (0, 5), (-10, 5), (-17, 15)],
    [(-10, 36), (-9, 43), (0, 48), (-2, 50), (5, 53), (8, 57), (12, 55), (18, 56),
     (21, 55), (24, 58), (28, 60), (30, 70), (40, 68), (45, 60), (40, 50), (30, 46),
     (25, 40), (20, 40), (15, 44), (10, 44), (3, 42), (-2, 37), (-10, 36)],
    [(30, 70), (50, 72), (70, 73), (90, 75), (110, 76), (130, 72), (150, 70), (170, 66),
     (178, 65), (170, 60), (160, 55), (155, 50), (145, 45), (140, 40), (135, 35),
     (128, 33), (122, 30), (118, 25), (110, 20), (105, 10), (100, 8), (95, 15),
     (90, 22), (85, 20), (80, 15), (75, 10), (70, 20), (65, 25), (60, 25), (55, 26),
     (50, 28), (48, 30), (44, 30), (40, 36), (35, 36), (30, 36), (30, 42), (30, 46),
     (28, 50), (30, 55), (30, 60), (30, 65), (30, 70)],
    [(100, 2), (104, -2), (108, -4), (104, -6), (100, -2)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32), (130, -32), (135, -35),
     (140, -38), (145, -38), (150, -37), (153, -32), (150, -25), (146, -20), (142, -15),
     (140, -12), (135, -12), (132, -11), (130, -13), (126, -14), (122, -17), (118, -20),
     (113, -22)],
    [(167, -45), (172, -41), (175, -38), (173, -42), (168, -46)],
]


def draw_map(d, x, y, w, h, numbered=9):
    d.rectangle([x, y, x + w, y + h], fill=SEA)
    d.rectangle([x, y, x + w, y + h], outline=LINE, width=1)
    # faint graticule: equator + meridians every 60 degrees
    ey = y + (78 - 0) / 136 * h
    d.line([(x, ey), (x + w, ey)], fill=(190, 205, 200), width=1)
    for lon in range(-120, 181, 60):
        gx = x + (lon + 168) / 360 * w
        d.line([(gx, y), (gx, y + h)], fill=(190, 205, 200), width=1)
    for poly in CONTINENTS:
        pts = [(x + (lon + 168) / 360 * w, y + (78 - lat) / 136 * h) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LAND_LINE)
    by_num = {s["n"]: s for s in STORIES}
    for n in range(1, 46):
        s = by_num[n]
        px = x + (s["lon"] + 168) / 360 * w
        py = y + (78 - s["lat"]) / 136 * h
        if n <= numbered:
            d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED, outline=(255, 255, 255), width=1)
            f = F(SANS_B, 9)
            t = str(n)
            tw = d.textlength(t, font=f)
            d.text((px - tw / 2, py - 5), t, font=f, fill=(255, 255, 255))
        else:
            d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=RED)


def masthead(d):
    f_title = F(SERIF_B, 56)
    t = "THE WORLD IN ONE DAY"
    tw = d.textlength(t, font=f_title)
    d.text(((W - tw) / 2, 16), t, font=f_title, fill=INK)
    f_date = F(SANS_B, 26)
    t2 = "TUESDAY  17  NOVEMBER  2026"
    tw2 = d.textlength(t2, font=f_date)
    d.text(((W - tw2) / 2, 82), t2, font=f_date, fill=RED)
    d.line([(M, 114), (W - M, 114)], fill=RED, width=3)
    return 122


def sub_lines_for(d, text, size, maxw, max_lines):
    """Wrap sub text, shrinking the font until it fits max_lines (min 9px)."""
    for sz in (size, size - 1, 9):
        f = F(SANS, sz)
        lines = wrap(d, text, f, maxw)
        if len(lines) <= max_lines:
            return f, lines
    f = F(SANS, 9)
    return f, wrap(d, text, f, maxw)[:max_lines]


def story_panel(d, s, x, y, w, h, icon_h, head_size=16, sub_size=12, sub_max=2, head_max=2):
    d.rectangle([x, y, x + w, y + h], outline=LINE, width=1)
    draw_icon(d, s, x + 1, y + 1, w - 2, icon_h)
    num_badge(d, x + 6, y + 6, s["n"])
    ty = y + icon_h + 7
    f, lines = fit_lines(d, s["head"], F(SANS_B, head_size), w - 14, head_max)
    ty = text_block(d, x + 7, ty, lines, f, INK)
    # sub gets only the lines that still fit inside the panel
    room = (y + h - 3) - (ty + 2)
    max_sub = max(0, min(sub_max, room // 11))
    if max_sub:
        sf, sub_lines = sub_lines_for(d, s["sub"], sub_size, w - 14, max_sub)
        text_block(d, x + 7, ty + 2, sub_lines, sf, MUTED)


def compact_cell(d, s, x, y, w):
    f = F(SANS_B, 12)
    n = str(s["n"])
    nw = d.textlength(n + "  ", font=f)
    d.text((x, y), n, font=f, fill=RED)
    head = s["head"]
    # shrink headline until it fits one line
    size = 12
    while size > 10:
        ff = F(SANS_B, size)
        if d.textlength(head, font=ff) <= w - nw - 2:
            break
        size -= 1
    d.text((x + nw, y), head, font=F(SANS_B, size), fill=INK)
    return y + 17


def compact_cell2(d, s, x, y, w):
    """Headline + one full-sentence sub, both on one line each."""
    f = F(SANS_B, 11)
    n = str(s["n"])
    nw = d.textlength(n + "  ", font=f)
    d.text((x, y), n, font=f, fill=RED)
    size = 11
    while size > 10:
        ff = F(SANS_B, size)
        if d.textlength(s["head"], font=ff) <= w - nw - 2:
            break
        size -= 1
    d.text((x + nw, y), s["head"], font=F(SANS_B, size), fill=INK)
    avail = w - nw - 2
    sf = F(SANS, 10)
    if d.textlength(s["sub"], font=sf) > avail:
        sf = F(SANS, 9)
    d.text((x + nw, y + 13), s["sub"], font=sf, fill=MUTED)
    return y + 26


def grain(img):
    """Deterministic newsprint speckle on the paper (fixed seed)."""
    import random
    dd = ImageDraw.Draw(img)
    rnd = random.Random(20261117)
    for _ in range(6000):
        gx = rnd.randint(0, W - 1)
        gy = rnd.randint(0, H - 1)
        c = (236, 230, 214) if rnd.random() < 0.5 else (252, 248, 236)
        dd.point((gx, gy), fill=c)


def stipple(d, x, y, w, h, color, n=90, seed=0):
    """Deterministic Ben-Day style dots inside a rect (fixed seed per panel)."""
    import random
    rnd = random.Random(777000 + seed)
    for _ in range(n):
        px = rnd.randint(x + 2, x + w - 3)
        py = rnd.randint(y + 2, y + h - 3)
        d.point((px, py), fill=color)


# ---------------------------------------------------------------- variant A
def build_A():
    """Front page v2: lead + 13 illustrated stories (1 lead, 8 full panels,
    4 small panels) + 32 more stories with one-sentence summaries + map.
    Layout: masthead 122 | lead 128-260 | rows 268-408, 416-556, 564-656 |
    label 664-692 | compact 692-900 | map label 908 | map 926-1006 | footer."""
    img = Image.new("RGB", (W, H), PAPER)
    grain(img)
    d = ImageDraw.Draw(img)
    y = masthead(d)
    s1 = STORIES[0]
    # lead: big scene left, two-sentence summary right
    ly, lh = 128, 132
    draw_icon(d, s1, M, ly, 300, lh)
    d.rectangle([M, ly, M + 300, ly + lh], outline=LINE, width=1)
    num_badge(d, M + 8, ly + 8, 1, r=13)
    tx = M + 316
    d.text((tx, ly + 2), "1  \u2022  LEAD \u2014 UKRAINE, EUROPE", font=F(SANS_B, 13), fill=RED)
    f, lines = fit_lines(d, s1["head"], F(SERIF_B, 38), W - M - tx, 2)
    ty = text_block(d, tx, ly + 22, lines, f, INK)
    sf = F(SANS, 15)
    sub_lines = wrap(d, s1["sub"], sf, W - M - tx)[:3]
    text_block(d, tx, ty + 6, sub_lines, sf, MUTED)
    # illustrated rows: stories 2-5 and 6-9, full panels with 3-line subs
    for row, stories in enumerate((STORIES[1:5], STORIES[5:9])):
        ry = 268 + row * 148
        for i, s in enumerate(stories):
            story_panel(d, s, M + i * 244, ry, 232, 140, 56,
                        head_size=15, sub_size=10, sub_max=3)
    # small illustrated row: stories 10-13 (football scoreboards + Rwanda hub)
    for i, s in enumerate(STORIES[9:13]):
        story_panel(d, s, M + i * 244, 564, 232, 92, 42,
                    head_size=13, sub_size=9, sub_max=2, head_max=1)
    y = 664
    y = section_label(d, M, y, "THE REST OF THE DAY  \u2014  32 MORE STORIES")
    gy = y
    for col in range(4):
        cx = M + col * 244
        for r in range(8):
            s = STORIES[13 + col * 8 + r]
            compact_cell2(d, s, cx, gy + r * 26, 233)
    y = 908
    d.text((M, y), "WHERE IT HAPPENED \u2014 17 NOVEMBER 2026  (red dots: stories 1\u201345, numbered 1\u20139)",
           font=F(SANS_B, 12), fill=RED)
    draw_map(d, M, y + 18, CW, 80)
    d.text((M, 1012), "45 STORIES  \u2022  TUESDAY 17 NOVEMBER 2026  \u2022  SOURCES: REUTERS, AP, BLOOMBERG, BBC, UN NEWS, LE MONDE",
           font=F(SANS, 10), fill=MUTED)
    return img


# ---------------------------------------------------------------- variant B
def build_B():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    y = masthead(d)
    s1 = STORIES[0]
    # lead band: big illustration, headline below
    draw_icon(d, s1, M, y, CW, 150)
    d.rectangle([M, y, M + CW, y + 150], outline=LINE, width=1)
    num_badge(d, M + 8, y + 8, 1, r=13)
    ty = y + 158
    f, lines = fit_lines(d, s1["head"], F(SERIF_B, 42), CW, 1)
    ty = text_block(d, M, ty, lines, f, INK)
    sf = F(SANS, 19)
    sub_lines = wrap(d, s1["sub"], sf, CW)[:1]
    text_block(d, M, ty + 4, sub_lines, sf, MUTED)
    # illustrated grid: 3 rows x 4, stories 2-13
    gy = 360
    for row in range(3):
        ry = gy + row * 140
        for i in range(4):
            s = STORIES[1 + row * 4 + i]
            story_panel(d, s, M + i * 244, ry, 232, 132, 78, head_size=15, sub_size=11, sub_max=1)
    # compact: 2 cols x 10 rows, stories 14-33
    y = 788
    y = section_label(d, M, y, "MORE FROM THE DAY  —  20 STORIES")
    gy = y
    for col in range(2):
        cx = M + col * 488
        for r in range(10):
            s = STORIES[13 + col * 10 + r]
            compact_cell(d, s, cx, gy + r * 16, 476)
    # map strip is omitted in B (visual-led); footer counts the stories
    d.text((M, 1004), "33 STORIES  •  TUESDAY 17 NOVEMBER 2026  •  SOURCES: REUTERS, AP, BLOOMBERG, BBC, UN NEWS, LE MONDE",
           font=F(SANS, 10), fill=MUTED)
    return img


# ---------------------------------------------------------------- variant C
def build_C():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    y = masthead(d)
    # numbers strip
    y = section_label(d, M, y, "THE DAY IN NUMBERS")
    bw = (CW - 4 * 8) // 5
    for i, (big, label) in enumerate(NUMBERS):
        bx = M + i * (bw + 8)
        d.rectangle([bx, y, bx + bw, y + 84], outline=LINE, width=1)
        bf = F(SANS_B, 30)
        tw = d.textlength(big, font=bf)
        d.text((bx + (bw - tw) / 2, y + 8), big, font=bf, fill=RED)
        lf = F(SANS, 12)
        ll = wrap(d, label, lf, bw - 16)[:2]
        ly = y + 46
        for ln in ll:
            lw = d.textlength(ln, font=lf)
            d.text((bx + (bw - lw) / 2, ly), ln, font=lf, fill=INK)
            ly += 15
    # timeline: 10 events
    y = 232
    y = section_label(d, M, y, "THE DAY, HOUR BY HOUR")
    ty = y
    for i, (part, n) in enumerate(TIMELINE):
        s = STORIES[n - 1]
        ry = ty + i * 24
        first = (i == 0)
        d.rectangle([M, ry, M + 108, ry + 20], fill=RED if first else (255, 255, 255),
                    outline=RED, width=1)
        pf = F(SANS_B, 11)
        pw = d.textlength(part, font=pf)
        d.text((M + (108 - pw) / 2, ry + 3), part, font=pf,
               fill=(255, 255, 255) if first else RED)
        hf = F(SANS_B, 15 if first else 14)
        d.text((M + 120, ry + 2), f"{s['n']}. {s['head']}", font=hf, fill=INK)
        sf = F(SANS, 12)
        d.text((M + 120, ry + 2), "", font=sf, fill=MUTED)
    # illustrated row: 6 panels, stories 12-17
    y = 508
    for i in range(6):
        s = STORIES[11 + i]
        story_panel(d, s, M + i * 163, y, 156, 150, 80, head_size=13, sub_size=11)
    # compact: stories 18-45 EXCLUDING the ones already in the timeline (19, 23, 28)
    # -> 25 distinct stories; timeline 10 + illustrated 6 + compact 25 = 41 distinct
    y = 666
    y = section_label(d, M, y, "AND THE REST OF THE DAY  —  25 MORE STORIES")
    gy = y
    rest = [s for s in STORIES[17:45] if s["n"] not in (19, 23, 28)]
    assert len(rest) == 25, len(rest)
    for col in range(3):
        cx = M + col * 324
        col_stories = rest[col * 9:(col + 1) * 9]
        for r, s in enumerate(col_stories):
            compact_cell(d, s, cx, gy + r * 17, 312)
    y = 850
    d.text((M, y), "WHERE IT HAPPENED — 17 NOVEMBER 2026  (red dots: stories 1–45, numbered 1–9)",
           font=F(SANS_B, 12), fill=RED)
    draw_map(d, M, y + 16, CW, 124)
    d.text((M, 998), "41 STORIES  •  TUESDAY 17 NOVEMBER 2026  •  SOURCES: REUTERS, AP, BLOOMBERG, BBC, UN NEWS, LE MONDE",
           font=F(SANS, 10), fill=MUTED)
    return img


BUILDERS = {"A": build_A, "B": build_B, "C": build_C}

if __name__ == "__main__":
    variant = sys.argv[1].upper()
    outdir = Path(__file__).parent.parent / "candidates" / variant
    outdir.mkdir(parents=True, exist_ok=True)
    img = BUILDERS[variant]()
    out = outdir / "entry.png"
    img.save(out, "PNG")
    print(f"{variant}: {out} {img.size} {out.stat().st_size} bytes")
