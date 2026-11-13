"""Retro Cafe lockup, built from the new logo PNG (assets/logo-new.png).

Two usable pieces:
  mark()     - just the vinyl-record mascot (circular brand mark)
  lockup()   - the full "RETR + mascot + CAFE · NASIM SHAHR" lockup
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from lib import AMBER, BRAND_RED, CREAM, HERE, W

LOGO_PATH = os.path.join(HERE, "assets", "logo-new.png")

# mascot disc bbox inside the alpha-trimmed logo (x0, y0, x1, y1)
MASCOT = (1012, 26, 1252, 268)

_src = {}


def _load():
    if "im" not in _src:
        im = Image.open(LOGO_PATH).convert("RGBA")
        im = im.crop(im.split()[3].getbbox())
        _src["im"] = im
    return _src["im"]


def mark(size):
    """The circular mascot, sized to `size` px square."""
    im = _load().crop(MASCOT)
    return im.resize((size, size), Image.LANCZOS)


def lockup(width, mode="dark"):
    """Full logo at `width` px.

    mode="dark"  -> recoloured for dark backgrounds: the wordmark becomes cream
                    and the thin rules become amber; the mascot keeps its colours.
    mode="red"   -> as drawn (brand red wordmark), for cream/light backgrounds.
    """
    im = _load().copy()
    w, h = im.size
    rgb = np.asarray(im.convert("RGB"), np.float32)
    a = np.asarray(im.split()[3], np.float32) / 255.0

    if mode == "dark":
        # mask: exclude the mascot square, keep only the text block on the left
        keep = np.ones((h, w), bool)
        keep[MASCOT[1]:MASCOT[3], MASCOT[0]:MASCOT[2]] = False
        # on the right of the wordmark the small "R" of RETR overlaps the mascot
        # column band; recover it by only excluding the mascot disc pixels
        keep[MASCOT[1]:MASCOT[3], MASCOT[0]:MASCOT[2]] = False
        lum = rgb.mean(2)
        k = (keep & (a > 0.15) & (lum < 200))[..., None]
        lit = rgb * (1 - k) + np.array(CREAM, np.float32) * k
        # thin grey rules -> amber so they are not washed out
        grey = (keep & (a > 0.15) & (lum >= 60) & (lum < 110) & (rgb[..., 0] < 120))
        lit = np.where(grey[..., None], np.array(AMBER, np.float32), lit)
        rgb = lit

    out = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8), "RGBA")
    nh = max(1, int(round(h * width / w)))
    return out.resize((width, nh), Image.LANCZOS)


def badge(size=120):
    """Circular avatar badge: cream disc, brand-red ring, mascot inside."""
    u = 4
    S = size * u
    disc = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(disc)
    d.ellipse([0, 0, S - 1, S - 1], fill=CREAM + (255,))
    d.ellipse([int(S * .02), int(S * .02), int(S * .98), int(S * .98)],
              outline=BRAND_RED + (255,), width=int(S * .05))
    m = mark(int(S * 0.84))
    disc.alpha_composite(m, ((S - m.width) // 2, (S - m.height) // 2))
    return disc.resize((size, size), Image.LANCZOS)


def watermark(img, size=88, margin=42, alpha=200):
    b = badge(size)
    b.putalpha(b.split()[3].point(lambda v: int(v * alpha / 255)))
    # soft shadow so it reads on bright plates
    sh = Image.new("RGBA", (size + 24, size + 24), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 110), (12, 12), b)
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)),
                        (W - size - margin - 12, margin - 12))
    img.alpha_composite(b, (W - size - margin, margin))
