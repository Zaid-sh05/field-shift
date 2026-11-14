"""Background art and logo prep for the Field Shift pitch deck (dark green theme)."""
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 2667, 1500
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
MINT, GOLD = (46, 230, 160), (242, 181, 68)


def gradient(top, bottom):
    t = np.linspace(0, 1, H)[:, None, None]
    img = np.array(top)[None, None, :] * (1 - t) + np.array(bottom)[None, None, :] * t
    return Image.fromarray(np.repeat(img, W, axis=1).astype("uint8"), "RGB")


def glow(base, draw_fn, blur, strength=1.0, crisp=True):
    """Draw on a transparent layer, blur it for a halo, then (unless crisp=False) draw the sharp version on top."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    halo = layer.filter(ImageFilter.GaussianBlur(blur))
    if strength != 1.0:
        halo.putalpha(halo.getchannel("A").point(lambda a: int(min(255, a * strength))))
    base.alpha_composite(halo)
    if crisp:
        base.alpha_composite(layer)


def stars(img, count, max_y, seed):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    for _ in range(count):
        x, y, r = rnd.randrange(W), rnd.randrange(int(max_y)), rnd.choice([1, 1, 1, 2, 2, 3])
        a = rnd.randrange(60, 200)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 255, 240, a))


def furrows(d, horizon, alpha, color, vanish_x=W * 0.5, count=34):
    """Field rows converging on a vanishing point, plus cross rows that tighten towards the horizon."""
    for i in range(count + 1):
        x_bottom = -W * 0.9 + i * (W * 2.8 / count)
        d.line([(vanish_x, horizon), (x_bottom, H)], fill=(*color, alpha), width=3)
    for k in range(1, 15):
        y = horizon + (H - horizon) * (k / 15) ** 2.2
        d.line([(0, y), (W, y)], fill=(*color, int(alpha * 0.55)), width=2)


def contours(d, alpha, seed, rows=9, y0=0.12, y1=0.9):
    rnd = random.Random(seed)
    for r in range(rows):
        base_y = H * (y0 + (y1 - y0) * r / (rows - 1))
        phase, amp, freq = rnd.uniform(0, 6.28), rnd.uniform(18, 46), rnd.uniform(0.0016, 0.003)
        pts = [(x, base_y + amp * math.sin(x * freq + phase) + 0.5 * amp * math.sin(x * freq * 2.3 + phase * 1.7)) for x in range(0, W + 30, 30)]
        d.line(pts, fill=(*MINT, alpha), width=2)


def orbit(d, cx, cy, rx, ry, tilt_deg, alpha, width=4, dash=(26, 22)):
    tilt = math.radians(tilt_deg)
    pts = []
    for i in range(0, 721):
        a = math.radians(i / 2)
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + x * math.cos(tilt) - y * math.sin(tilt), cy + x * math.sin(tilt) + y * math.cos(tilt)))
    step = dash[0] + dash[1]
    for i in range(0, len(pts) - 1):
        if (i * 6) % step < dash[0]:
            d.line([pts[i], pts[i + 1]], fill=(*MINT, alpha), width=width)
    return pts


def satellite(d, x, y, scale=1.0):
    s = scale
    d.rounded_rectangle([x - 26 * s, y - 18 * s, x + 26 * s, y + 18 * s], radius=6 * s, fill=(240, 255, 248, 255))
    for side in (-1, 1):
        d.rectangle([x + side * 34 * s - 28 * s * (side < 0), y - 12 * s, x + side * 34 * s + 28 * s * (side > 0), y + 12 * s], fill=(*MINT, 255))
        d.line([(x + side * 26 * s, y), (x + side * 34 * s, y)], fill=(240, 255, 248, 255), width=max(2, int(3 * s)))
    d.line([(x, y + 18 * s), (x, y + 34 * s)], fill=(240, 255, 248, 255), width=max(2, int(3 * s)))
    d.ellipse([x - 8 * s, y + 30 * s, x + 8 * s, y + 46 * s], fill=(*GOLD, 255))


def vignette(img, bottom_from=0.76, strength=0.72):
    """Darken the bottom band so footer and source text stay readable."""
    arr = np.asarray(img.convert("RGB")).astype("float32")
    y = np.linspace(0, 1, H)[:, None, None]
    k = np.clip((y - bottom_from) / (1 - bottom_from), 0, 1) * strength
    return Image.fromarray((arr * (1 - k)).astype("uint8"), "RGB")


def cover():
    img = gradient((3, 20, 15), (8, 58, 42)).convert("RGBA")
    stars(img, 420, H * 0.55, seed=7)
    horizon = H * 0.60
    # horizon glow: the sun rising behind the fields
    glow(img, lambda d: d.ellipse([W * 0.5 - 520, horizon - 150, W * 0.5 + 520, horizon + 150], fill=(*GOLD, 110)), blur=150, crisp=False)
    glow(img, lambda d: d.ellipse([W * 0.5 - 1500, horizon - 40, W * 0.5 + 1500, horizon + 40], fill=(*MINT, 120)), blur=70, crisp=False)
    ground = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(ground)
    gd.rectangle([0, horizon, W, H], fill=(5, 38, 28, 235))
    img.alpha_composite(ground)
    glow(img, lambda d: furrows(d, horizon, 120, MINT), blur=6, strength=0.9)
    # orbit and satellite, upper right
    def sky(d):
        # kept clear of the top-right corner, where the team logo sits
        pts = orbit(d, W * 0.60, H * 0.33, 470, 150, -14, 150)
        orbit(d, W * 0.60, H * 0.33, 640, 215, -14, 60, width=2, dash=(10, 26))
        satellite(d, *pts[60], scale=1.4)
    glow(img, sky, blur=10, strength=1.3)
    # darken the left side of the ground so the tagline and team names read cleanly over the field rows
    arr = np.asarray(img.convert("RGB")).astype("float32")
    x = np.linspace(0, 1, W)[None, :, None]
    y = np.linspace(0, 1, H)[:, None, None]
    shade = np.clip(1 - x / 0.72, 0, 1) * np.clip((y - 0.5) / 0.12, 0, 1) * 0.62
    img = Image.fromarray((arr * (1 - shade)).astype("uint8"), "RGB")
    return vignette(img, bottom_from=0.80, strength=0.55)


def content(seed, with_orbit=True):
    img = gradient((3, 20, 15), (6, 44, 32)).convert("RGBA")
    stars(img, 70, H * 0.42, seed=seed)
    glow(img, lambda d: contours(d, 20, seed), blur=3)
    horizon = H * 0.86
    ground = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ground).rectangle([0, horizon, W, H], fill=(5, 38, 28, 150))
    img.alpha_composite(ground)
    glow(img, lambda d: furrows(d, horizon, 38, MINT, vanish_x=W * (0.3 + 0.1 * (seed % 5))), blur=4)
    if with_orbit:
        glow(img, lambda d: orbit(d, W * 0.86, H * 0.08, 520, 150, -12, 46, width=3), blur=6)
    return vignette(img, bottom_from=0.74, strength=0.7)


def team_logo(src):
    """The logo sits on black: turn darkness into transparency so it floats on the deck's background."""
    rgb = Image.open(src).convert("RGB")
    arr = np.asarray(rgb).astype("float32")
    alpha = np.clip((arr.max(axis=2) - 14) * 1.5, 0, 255).astype("uint8")
    out = Image.fromarray(np.dstack([np.asarray(rgb), alpha]), "RGBA")
    return out.crop(out.getbbox())


if __name__ == "__main__":
    cover().save(OUT / "bg_cover.jpg", quality=90)
    for n in range(2, 8):
        content(seed=n, with_orbit=n % 2 == 0).save(OUT / f"bg_{n}.jpg", quality=88)
    team_logo(sys.argv[2]).save(OUT / "logo_team.png")
    space = Image.open(sys.argv[3]).convert("RGBA")
    space.crop(space.getbbox()).save(OUT / "logo_spaceapps.png")
    print("art written to", OUT)
