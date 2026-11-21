#!/usr/bin/env python3
"""AURELIA — the waterfall that falls UP. Travel poster for a place that does not exist.

Draws the poster entirely in code (Pillow, no network, deterministic) and writes
/output/entry.png (1024x1024 PNG). One landmark only: a great waterfall rising
from a lagoon into the clouds at golden hour. The only text is the place name.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 1024
HORIZON = 640  # lagoon surface
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

# Palette: warm gold/amber sky, rose clouds, teal-green lagoon, white-gold mist.
SKY_TOP = (176, 96, 34)
SKY_MID = (232, 163, 76)
SKY_LOW = (242, 192, 120)
SKY_HORIZON = (251, 227, 176)
SUN_CORE = (255, 217, 138)
SUN_GLOW = (255, 190, 90)
CLOUD_ROSE = (233, 138, 122)
CLOUD_CREAM = (250, 214, 170)
CLIFF = (20, 56, 46)
CLIFF_RIM = (212, 150, 80)
LAGOON_TOP = (46, 125, 107)
LAGOON_BOT = (24, 88, 72)
WATER_CORE = (255, 255, 255)
WATER_WARM = (255, 233, 184)
MIST = (255, 250, 238)
NAME_CREAM = (255, 246, 224)
NAME_SHADOW = (122, 74, 30)
BOAT = (26, 34, 30)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky_gradient(draw):
    """Golden-hour sky, warm at top, pale at the horizon."""
    for y in range(HORIZON):
        if y < HORIZON * 0.45:
            c = lerp(SKY_TOP, SKY_MID, y / (HORIZON * 0.45))
        elif y < HORIZON * 0.8:
            c = lerp(SKY_MID, SKY_LOW, (y - HORIZON * 0.45) / (HORIZON * 0.35))
        else:
            c = lerp(SKY_LOW, SKY_HORIZON, (y - HORIZON * 0.8) / (HORIZON * 0.2))
        draw.line([(0, y), (SIZE, y)], fill=c)


def soft_ellipse(base, box, fill, blur):
    """Draw a soft blurred ellipse on an RGBA overlay and composite it."""
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.ellipse(box, fill=fill)
    ov = ov.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(ov)


def sun(base):
    """Low golden sun with a warm glow, right of the falls."""
    cx, cy, r = 770, 470, 54
    soft_ellipse(base, [cx - 150, cy - 150, cx + 150, cy + 150],
                 SUN_GLOW + (70,), 60)
    soft_ellipse(base, [cx - 95, cy - 95, cx + 95, cy + 95],
                 SUN_GLOW + (120,), 30)
    d = ImageDraw.Draw(base)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUN_CORE + (255,))
    d.ellipse([cx - r + 10, cy - r + 12, cx + r - 10, cy + r - 10],
              fill=(255, 232, 170, 255))


def clouds(base):
    """A few soft rose/cream clouds, low and wide."""
    for (x, y, w, h, col, a) in [
        (60, 300, 260, 46, CLOUD_ROSE, 150),
        (120, 330, 200, 38, CLOUD_CREAM, 130),
        (700, 210, 280, 50, CLOUD_ROSE, 140),
        (760, 245, 190, 36, CLOUD_CREAM, 120),
        (330, 180, 180, 32, CLOUD_CREAM, 100),
    ]:
        soft_ellipse(base, [x, y, x + w, y + h], col + (a,), 14)


def cliffs(base):
    """Dark green headlands framing the falls, with soft curved tops."""
    d = ImageDraw.Draw(base)
    left = [(0, HORIZON), (0, 468)]
    for x in range(0, 245, 8):
        t = x / 245.0
        y = 468 + (HORIZON - 468) * (t ** 1.5) + 10 * math.sin(t * 9.0)
        left.append((x, y))
    left.append((245, HORIZON))
    d.polygon(left, fill=CLIFF + (255,))
    right = [(SIZE, HORIZON), (SIZE, 478)]
    for x in range(SIZE, 780, -8):
        t = (SIZE - x) / 244.0
        y = 478 + (HORIZON - 478) * (t ** 1.5) + 10 * math.sin(t * 8.0 + 2.0)
        right.append((x, y))
    right.append((780, HORIZON))
    d.polygon(right, fill=CLIFF + (255,))
    # Warm rim light along the curved inner edges, catching the low sun.
    d.line(left[2:-1], fill=CLIFF_RIM + (200,), width=4)
    d.line(right[2:-1], fill=CLIFF_RIM + (200,), width=4)


def lagoon(base):
    """Teal-green lagoon with a warm sun reflection and gentle ripples."""
    d = ImageDraw.Draw(base)
    for y in range(HORIZON, SIZE):
        t = (y - HORIZON) / (SIZE - HORIZON)
        d.line([(0, y), (SIZE, y)], fill=lerp(LAGOON_TOP, LAGOON_BOT, t) + (255,))
    # Sun reflection: stacked horizontal gold dashes under the sun,
    # widening as they run down the water — a shimmering path, not a band.
    rng = random.Random(20261121)
    for i, y in enumerate(range(HORIZON + 14, SIZE - 16, 16)):
        w = 26 + i * 7
        a = max(40, 150 - i * 6)
        x0 = 770 - w // 2 + rng.randint(-8, 8)
        d.line([(x0, y), (x0 + w, y)], fill=(247, 200, 115, a), width=3)
    # Ripples: few, thin, in loose horizontal bands — water, not confetti.
    for _ in range(34):
        x = rng.randint(40, SIZE - 40)
        y = rng.randint(HORIZON + 12, SIZE - 20)
        ln = rng.randint(26, 70)
        near = max(0, 1 - abs(x - 770) / 420)
        a = int(28 + 55 * near + rng.randint(0, 20))
        d.line([(x, y), (x + ln, y)], fill=(255, 240, 200, a), width=2)


def column_width(y):
    """The rising column: WIDE at the lagoon, narrowing as it climbs.
    A falling waterfall does the opposite (narrow at the lip, spreading at
    the base) — this taper is the first cue that the water goes UP."""
    t = (HORIZON - y) / (HORIZON - 200)  # 0 at lagoon, 1 at the cloud
    t = max(0.0, min(1.0, t))
    return 320 - 280 * (t ** 1.15)


def rising_falls(base):
    """The waterfall that falls up: wide foam base, narrowing bright column,
    dissolving into cloud at the top. Spray and mist billow UPWARD."""
    rng = random.Random(20261121)
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    # Outer mist sleeve around the column.
    for y in range(245, HORIZON, 6):
        w = column_width(y) * 0.72
        sway = 8 * math.sin(y * 0.018) + 5 * math.sin(y * 0.043 + 1.7)
        cx = 512 + sway
        od.ellipse([cx - w, y - 4, cx + w, y + 8], fill=MIST + (46,))
    ov = ov.filter(ImageFilter.GaussianBlur(10))
    base.alpha_composite(ov)
    # Main column, wavy edges, bright core.
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    left, right = [], []
    for y in range(245, HORIZON + 1, 4):
        w = column_width(y) * 0.5
        sway = 8 * math.sin(y * 0.018) + 5 * math.sin(y * 0.043 + 1.7)
        left.append((512 - w + sway, y))
        right.append((512 + w + sway, y))
    od.polygon(left + right[::-1], fill=(245, 252, 250, 235))
    # Bright core, narrower, warm at the base where the sun hits it.
    left2, right2 = [], []
    for y in range(255, HORIZON + 1, 4):
        w = column_width(y) * 0.22
        sway = 8 * math.sin(y * 0.018) + 5 * math.sin(y * 0.043 + 1.7)
        left2.append((512 - w + sway, y))
        right2.append((512 + w + sway, y))
    od.polygon(left2 + right2[::-1], fill=WATER_CORE + (255,))
    ov = ov.filter(ImageFilter.GaussianBlur(2))
    base.alpha_composite(ov)
    # Warm rim light on the sunlit (right) edge of the column — a thin
    # strip, not a block, so it reads as light on moving water.
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    strip = []
    for y in range(255, HORIZON + 1, 4):
        w = column_width(y) * 0.5
        sway = 8 * math.sin(y * 0.018) + 5 * math.sin(y * 0.043 + 1.7)
        strip.append((512 + w * 0.72 + sway, y))
    for (x, y) in strip:
        od.ellipse([x - 7, y - 3, x + 7, y + 3], fill=WATER_WARM + (150,))
    ov = ov.filter(ImageFilter.GaussianBlur(3))
    base.alpha_composite(ov)
    # Upward flow: a few short, thick streaks in the lower column only —
    # water visibly travelling UP, without scratching the whole sheet.
    d2 = ImageDraw.Draw(base)
    for k in range(5):
        frac = (k + 0.5) / 5.0
        x0 = 512 - 90 + frac * 180
        pts = []
        for y in range(HORIZON - 10, 380, -16):
            sway = 8 * math.sin(y * 0.018) + 5 * math.sin(y * 0.043 + 1.7)
            pts.append((x0 + sway * 0.4, y))
        d2.line(pts, fill=(255, 255, 255, 120), width=6)
    # Fountain burst: thick white jets radiating upward-outward from one
    # point on the lagoon surface, with a droplet at each tip — the water
    # LEAVES the lagoon, it does not land in it.
    for ang in (-75, -55, -35, -15, 0, 15, 35, 55, 75):
        rad = math.radians(ang)
        x1 = 512 + 40 * math.sin(rad)
        y1 = HORIZON - 6 - 12 * math.cos(rad)
        ln = 90 + (60 if abs(ang) < 20 else 0)
        x2 = 512 + (40 + ln) * math.sin(rad)
        y2 = y1 - ln * math.cos(rad)
        d2.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 220), width=8)
        d2.ellipse([x2 - 6, y2 - 6, x2 + 6, y2 + 6], fill=(255, 255, 255, 220))
    # Spray flung upward from the rising jet: droplets arcing up and out
    # from the column's top, each with its trail BELOW it — motion upward.
    for (x, y, r) in [(420, 262, 7), (395, 236, 6), (372, 210, 5),
                      (602, 258, 7), (626, 232, 6), (650, 206, 5)]:
        d2.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 230))
        d2.line([(x, y + r), (x, y + r + 16)], fill=(255, 255, 255, 160), width=3)
    # Spray streaks: short vertical marks angled slightly outward, rising
    # along the column edges, sparser as they climb.
    d = ImageDraw.Draw(base)
    for _ in range(70):
        y = rng.randint(200, HORIZON - 20)
        w = column_width(y) * 0.5
        side = rng.choice((-1, 1))
        x = 512 + side * w + rng.randint(-14, 14) + 14 * math.sin(y * 0.018)
        ln = rng.randint(10, 30)
        a = int(90 + rng.randint(0, 110))
        d.line([(x, y), (x + side * rng.randint(2, 8), y - ln)],
               fill=(255, 255, 255, a), width=3)
    # Foam crown where the water leaves the lagoon: the base is a splash
    # going UP, not a pool catching a fall.
    for (x, y, w, h, a) in [
        (330, 622, 364, 34, 200), (380, 636, 264, 26, 170),
        (420, 612, 184, 22, 150), (300, 640, 424, 24, 120),
    ]:
        soft_ellipse(base, [x, y, x + w, y + h], MIST + (a,), 8)


def top_cloud(base):
    """A proper cloud the rising water dissolves into: a cluster of
    overlapping white puffs sitting BELOW the name, with the column's
    top merging into its underside."""
    puffs = [
        (400, 215, 150, 56, 245), (500, 200, 170, 62, 250),
        (330, 245, 130, 48, 235), (560, 240, 140, 50, 235),
        (450, 245, 160, 52, 240), (380, 272, 120, 42, 215),
        (540, 270, 120, 42, 215),
    ]
    for (x, y, w, h, a) in puffs:
        soft_ellipse(base, [x, y, x + w, y + h], (255, 253, 248, a), 5)
    # Crisp bright cores so the puffs read as cloud, not a smudge.
    d = ImageDraw.Draw(base)
    for (cx, cy, r) in [(470, 232, 34), (540, 222, 30), (420, 248, 26),
                        (580, 250, 24), (500, 258, 28), (450, 268, 22)]:
        d.ellipse([cx - r, cy - r, cx + r, cy - r + r * 0.7],
                  fill=(255, 253, 248, 235))


def birds(base):
    """Small birds rising with the water, ascending left of the column."""
    d = ImageDraw.Draw(base)
    for (x, y, s) in [(350, 545, 14), (370, 470, 13), (390, 395, 12), (410, 325, 11)]:
        d.line([(x - s, y), (x, y - s * 0.55), (x + s, y)],
               fill=(42, 42, 42, 210), width=3)


def boat(base):
    """A tiny boat with one figure at the base of the falls — scale, and
    the promise of the stay: warm light on the lagoon, mist to stand in."""
    d = ImageDraw.Draw(base)
    x, y = 648, 706
    d.polygon([(x - 26, y), (x + 26, y), (x + 18, y + 12), (x - 18, y + 12)],
              fill=BOAT + (255,))
    d.line([(x - 26, y), (x + 26, y)], fill=(247, 200, 115, 220), width=2)
    # One seated figure, dark silhouette with a warm rim.
    d.ellipse([x - 4, y - 16, x + 4, y - 8], fill=BOAT + (255,))   # head
    d.polygon([(x - 7, y - 2), (x + 7, y - 2), (x + 4, y - 9), (x - 4, y - 9)],
              fill=BOAT + (255,))                                  # body
    d.line([(x + 8, y - 6), (x + 22, y + 8)], fill=BOAT + (255,), width=2)  # oar
    # A faint wake trailing behind the boat.
    d.line([(x - 30, y + 12), (x - 70, y + 14)], fill=(255, 240, 200, 90), width=2)


def name(base):
    """AURELIA, huge across the upper sky, warm cream, tracked."""
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSansDisplay-ExtraBold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-ExtraBold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    font = None
    for p in paths:
        try:
            font = ImageFont.truetype(p, 128)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    text = "AURELIA"
    tracking = 20
    d = ImageDraw.Draw(base)
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (SIZE - total) // 2
    y = 44
    for ch, w in zip(text, widths):
        d.text((x + 5, y + 7), ch, font=font, fill=NAME_SHADOW + (255,))
        d.text((x, y), ch, font=font, fill=NAME_CREAM + (255,))
        x += w + tracking


def render(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    sky_gradient(d)
    sun(img)
    clouds(img)
    cliffs(img)
    lagoon(img)
    rising_falls(img)
    top_cloud(img)
    birds(img)
    boat(img)
    name(img)
    return img.convert("RGB")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for size in (SIZE, 896, 768):
        img = render(size)
        path = os.path.join(OUT_DIR, "entry.png")
        img.save(path, format="PNG", optimize=True)
        if os.path.getsize(path) <= 1_048_576:
            return
    raise SystemExit("entry.png exceeds 1 MiB at every size")


if __name__ == "__main__":
    main()
