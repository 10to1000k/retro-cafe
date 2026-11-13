#!/usr/bin/env python3
"""Render the 1800 frames of the 60 s reel, plus QA contact sheets.

usage:  python3 render.py [sheet]
"""
import json
import os
import sys

import numpy as np
from PIL import Image

import scenes
from lib import H, W, fade_io, grain
from logo import watermark

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(HERE, "frames")
FPS = 30
DUR = 60.0
N = int(DUR * FPS)

TL = json.load(open(os.path.join(HERE, "timeline.json")))
BOUNDS = TL["bounds"]
NAMES = [n for n, _ in scenes.SCENES]
FNS = [f for _, f in scenes.SCENES]
assert len(BOUNDS) == len(FNS) + 1, (len(BOUNDS), len(FNS))


def build_frame(i):
    t = i / FPS
    k = max(0, min(len(FNS) - 1, int(np.searchsorted(BOUNDS[1:], t, side="right"))))
    a, b = BOUNDS[k], BOUNDS[k + 1]
    img = FNS[k](t, a, b)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    # global fade in / out
    f = fade_io(t, DUR, 0.7, 1.1)
    if f < 1:
        black = Image.new("RGBA", (W, H), (8, 5, 3, 255))
        img = Image.blend(black, img, max(0.0, f))
    if k not in (0, len(FNS) - 1) or t > 2.0:
        watermark(img, size=92, margin=44, alpha=190)
    out = Image.fromarray(grain(img, 3, seed=i % 17), "RGB")
    return out


def frame_one(i, check=False):
    p = os.path.join(FRAMES, f"f{i:05d}.jpg")
    if check and os.path.exists(p):
        return
    build_frame(i).save(p, quality=92, subsampling=0)


def main():
    os.makedirs(FRAMES, exist_ok=True)
    todo = [i for i in range(N) if not os.path.exists(os.path.join(FRAMES, f"f{i:05d}.jpg"))]
    print(f"{len(todo)} frames to render")
    for n, i in enumerate(todo):
        frame_one(i)
        if n % 100 == 0:
            print(f"  {n}/{len(todo)}", flush=True)
    miss = [i for i in range(N) if not os.path.exists(os.path.join(FRAMES, f"f{i:05d}.jpg"))]
    print("missing:", miss)
    for i in miss:
        frame_one(i)
    print("done")


def sheet(idx, path, cols=5, tw=300):
    th = int(tw * H / W)
    rows = (len(idx) + cols - 1) // cols
    sh = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
    for n, i in enumerate(idx):
        im = Image.open(os.path.join(FRAMES, f"f{i:05d}.jpg")).resize((tw, th), Image.LANCZOS)
        sh.paste(im, ((n % cols) * tw, (n // cols) * th))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sh.save(path, quality=90)
    print(path)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sheet":
        os.makedirs(os.path.join(HERE, "frames"), exist_ok=True)
        for k in range(len(FNS)):
            if not os.path.exists(os.path.join(FRAMES, f"f{int(BOUNDS[k] * FPS):05d}.jpg")):
                for i in range(int(BOUNDS[k] * FPS), min(N, int(BOUNDS[k + 1] * FPS))):
                    frame_one(i)
        idx = [int((BOUNDS[k] + BOUNDS[k + 1]) / 2 * FPS) for k in range(len(FNS))]
        sheet(idx, os.path.join(HERE, "test", "scenes.jpg"))
    else:
        main()
