#!/usr/bin/env python3
"""Mix VO + music at 48 kHz with envelope ducking under the narration."""
import json
import os
import subprocess
import wave

import imageio_ffmpeg
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
FF = imageio_ffmpeg.get_ffmpeg_exe()


def load_wav(path):
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-f", "s16le", "-ac", "2",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, "<i2").astype(np.float32) / 32768.0
    return x.reshape(-1, 2)


def main():
    tl = json.load(open(os.path.join(HERE, "timeline.json")))
    vo = np.load(os.path.join(HERE, "vo.npy")).astype(np.float32)
    n = len(vo)
    music = load_wav(os.path.join(HERE, "music.wav"))[:n]
    if len(music) < n:
        music = np.pad(music, ((0, n - len(music)), (0, 0)))

    # ducking envelope from the VO (fast attack, slow release)
    act = np.abs(vo)
    win = int(0.05 * SR)
    k = np.ones(win) / win
    env = np.convolve(act, k, "same")
    env = np.convolve(env, k, "same")
    env = env / (env.max() or 1)
    duck = 1.0 - 0.62 * np.clip(env * 3.2, 0, 1) ** 0.7
    duck = np.convolve(duck, np.ones(int(0.12 * SR)) / int(0.12 * SR), "same")

    music_lvl = 0.78
    mg = music * (duck * music_lvl)[:, None]

    vo_st = np.stack([vo, vo], 1)
    vo_st = vo_st / (np.max(np.abs(vo_st)) or 1) * 0.95
    mix = mg + vo_st
    # soft limit
    mix = np.tanh(mix * 1.05) * 0.96

    pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
    with wave.open(os.path.join(HERE, "mix.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"mix.wav {pcm.shape[0]/SR:.2f}s")

    # level report
    def db(x):
        return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    print(f"  VO rms {db(vo):.1f} dB  music rms {db(mg):.1f} dB  mix peak {np.abs(mix).max():.3f}")


if __name__ == "__main__":
    main()
