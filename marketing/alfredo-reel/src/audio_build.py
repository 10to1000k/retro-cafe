#!/usr/bin/env python3
"""Build the 60 s narration track from the per-line TTS clips.

The VO drives the edit: lines are laid out over 60 s with equal gaps, then each
scene boundary is placed in the middle of the silence between two lines. That
guarantees a line can never spill into the next scene's picture.

Outputs: vo.npy (48 kHz mono float32), timeline.json (vo + scene boundaries).
"""
import json
import os
import subprocess

import imageio_ffmpeg
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "audio")
SR = 48000
DUR = 60.0
N_SAMPLES = int(SR * DUR)

FF = imageio_ffmpeg.get_ffmpeg_exe()

SCENES = [
    ("hook", "v1.mp3"),
    ("rome", "v2.mp3"),
    ("dilelio", "v3.mp3"),
    ("three", "v4.mp3"),
    ("nosugar", "v5.mp3"),
    ("glam", "v6.mp3"),
    ("world", "v7.mp3"),
    ("usa", "v8.mp3"),
    ("retro1", "v9.mp3"),
    ("retro2", "v10.mp3"),
]


def decode(path):
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def trim(x, thresh=0.012, pad=0.045):
    a = np.abs(x)
    idx = np.nonzero(a > thresh)[0]
    if not len(idx):
        return x
    s = max(0, idx[0] - int(pad * SR))
    e = min(len(x), idx[-1] + int(pad * SR))
    return x[s:e]


def main():
    clips = []
    for sid, fn in SCENES:
        x = trim(decode(os.path.join(AUD, fn)))
        x = x / (np.max(np.abs(x)) or 1.0) * 0.92
        clips.append((sid, x))

    total = sum(len(x) / SR for _, x in clips)
    gap = (DUR - total) / (len(clips) + 1)
    if gap < 0.15:
        raise SystemExit(f"VO too long: {total:.2f}s speech leaves gap {gap:.3f}s")
    print(f"speech {total:.2f}s  gap {gap:.3f}s")

    vo = np.zeros(N_SAMPLES, dtype=np.float32)
    lines, cursor = [], gap
    for sid, x in clips:
        n = len(x)
        i0 = int(round(cursor * SR))
        assert i0 + n <= N_SAMPLES, sid
        vo[i0:i0 + n] += x
        f = int(0.012 * SR)
        vo[i0:i0 + f] *= np.linspace(0, 1, f)
        vo[i0 + n - f:i0 + n] *= np.linspace(1, 0, f)
        lines.append(dict(id=sid, start=round(cursor, 3), end=round(cursor + n / SR, 3)))
        cursor += n / SR + gap

    # scene boundaries sit in the middle of the silence between lines
    bounds = [0.0]
    for i in range(len(lines) - 1):
        bounds.append(round((lines[i]["end"] + lines[i + 1]["start"]) / 2, 3))
    bounds.append(DUR)

    np.save(os.path.join(HERE, "vo.npy"), vo)
    with open(os.path.join(HERE, "timeline.json"), "w") as f:
        json.dump(dict(duration=DUR, sr=SR, gap=round(gap, 3),
                       lines=lines, bounds=bounds), f, indent=2)
    for i, (sid, _) in enumerate(clips):
        print(f'  {sid:8s} scene {bounds[i]:6.2f}-{bounds[i+1]:6.2f}  '
              f'vo {lines[i]["start"]:6.2f}-{lines[i]["end"]:6.2f}')
    print("wrote vo.npy + timeline.json")


if __name__ == "__main__":
    main()
