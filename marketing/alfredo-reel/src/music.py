#!/usr/bin/env python3
"""60 s warm swing/bossa bed, synthesised from scratch (no samples)."""
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
DUR = 60.0
N = int(SR * DUR)
BPM = 100.0
BEAT = 60.0 / BPM

# Bb major 7 - Gm7 - Cm7 - F7 (ii-V-ish loop, cosy cafe feel)
CHORDS = [
    [58, 62, 65, 69],   # Bbmaj7
    [55, 58, 62, 65],   # Gm7
    [56, 60, 63, 67],   # Cm7 (lydian-ish colour)
    [53, 57, 60, 64],   # Fmaj7
]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a=0.01, d=0.4, s=0.5, r=0.15):
    t = np.arange(n) / SR
    e = np.ones(n)
    aa = int(a * SR)
    e[:aa] = np.linspace(0, 1, aa)
    dd = min(int(d * SR), max(0, n - aa))
    if dd:
        e[aa:aa + dd] = np.linspace(1, s, dd)
    e[aa + dd:] = s
    rr = int(r * SR)
    if rr:
        e[-rr:] *= np.linspace(1, 0, rr)
    return e


def epiano(m, dur, vel=1.0):
    """FM-ish electric piano (Rhodes flavour)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    mod = np.sin(2 * np.pi * f * 2 * t) * 1.2 * np.exp(-t * 6)
    x = np.sin(2 * np.pi * f * t + mod)
    x += 0.25 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 9)
    x += 0.10 * np.sin(2 * np.pi * f * 3 * t) * np.exp(-t * 14)
    return x * env(n, 0.006, 0.55, 0.35, 0.25) * vel


def bass(m, dur, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(4 * np.pi * f * t)
    x = np.tanh(x * 1.6)
    return x * env(n, 0.008, 0.18, 0.55, 0.12) * vel


def brush(dur, vel=1.0, seed=0):
    """Soft brushy noise hat / snare."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = rng.normal(0, 1, n)
    # crude band-pass
    x = np.convolve(x, np.ones(6) / 6, "same")
    x -= np.convolve(x, np.ones(60) / 60, "same")
    return x * env(n, 0.002, 0.05, 0.0, 0.06) * vel


def main():
    out = np.zeros(N, dtype=np.float64)
    beats = int(DUR / BEAT)
    for bi in range(beats):
        t0 = bi * BEAT
        bar = bi // 4
        beat_in_bar = bi % 4
        ch = CHORDS[bar % len(CHORDS)]
        i0 = int(t0 * SR)
        if i0 >= N:
            break

        # --- comp: chord on 1 and the "and" of 2 (swing feel)
        if beat_in_bar in (0, 2):
            for k, m in enumerate(ch):
                s = epiano(m, BEAT * (1.9 if beat_in_bar == 0 else 0.9),
                           vel=0.30 if beat_in_bar == 0 else 0.20)
                j = i0 + int((0.03 if beat_in_bar == 2 else 0) * SR)
                out[j:j + len(s)] += s[:max(0, N - j)]

        # --- bass: root on 1, fifth on 3
        if beat_in_bar == 0:
            s = bass(ch[0] - 12, BEAT * 1.7, 0.42)
            out[i0:i0 + len(s)] += s[:max(0, N - i0)]
        if beat_in_bar == 2:
            s = bass(ch[1] - 12, BEAT * 1.5, 0.34)
            out[i0:i0 + len(s)] += s[:max(0, N - i0)]

        # --- brushes
        if beat_in_bar in (1, 3):
            s = brush(BEAT * 0.5, 0.16, seed=bi)
            out[i0:i0 + len(s)] += s[:max(0, N - i0)]
        s = brush(BEAT * 0.12, 0.055 if beat_in_bar % 2 == 0 else 0.035, seed=bi + 99)
        j = i0 + int(BEAT / 2 * SR)
        out[j:j + len(s)] += s[:max(0, N - j)]

    # melody: sparse pentatonic-ish top line, phrases of 4 bars
    rng = np.random.default_rng(11)
    scale = [69, 72, 74, 77, 79, 81]
    t = 8 * BEAT
    while t < DUR - 2:
        bar = int(t / (4 * BEAT)) % len(CHORDS)
        notes = [rng.choice(scale), rng.choice(scale), rng.choice(scale)]
        for k, m in enumerate(notes):
            dur = BEAT * (1.0 if k < 2 else 1.6)
            s = epiano(m + 12, dur, 0.115)
            i0 = int((t + k * BEAT * 0.75) * SR)
            if i0 < N:
                out[i0:i0 + len(s)] += s[:max(0, N - i0)]
        t += 4 * BEAT * rng.choice([1, 1, 2])

    # soft pad underneath for glue
    tt = np.arange(N) / SR
    pad = np.zeros(N)
    for k, m in enumerate(CHORDS[0]):
        pad += np.sin(2 * np.pi * hz(m - 12) * tt + k)
    pad *= 0.012 * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 15))
    out += pad

    # gentle low-pass smoothing + master envelope
    out = np.convolve(out, np.ones(3) / 3, "same")
    fade = int(1.2 * SR)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-int(2.0 * SR):] *= np.linspace(1, 0, int(2.0 * SR))
    out = out / (np.max(np.abs(out)) or 1)
    out = np.tanh(out * 1.15) * 0.82

    st = np.stack([out, np.roll(out, int(0.008 * SR))], 1)
    pcm = (np.clip(st, -1, 1) * 32767).astype("<i2")
    import wave
    with wave.open(os.path.join(HERE, "music.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("music.wav", pcm.shape, f"{N/SR:.2f}s")


if __name__ == "__main__":
    main()
