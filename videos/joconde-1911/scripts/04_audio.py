#!/usr/bin/env python3
"""Audio : musique et bruitages synthétisés (libres de droits), ducking sous la voix, mastering, mesures.

Entrées  : build/voix.wav, build/chronologie.json, scripts/plans.json
Sorties  : build/stems/{voix,musique,bruitages}.wav (stéréo 48 kHz, niveaux du mix final : leur somme = le master)
           build/mix_master.wav (−14 LUFS intégrés, crête vraie ≤ −1,5 dBTP)
           build/audio_mesures.json (écart voix/musique, loudness, crête)
Tout est déterministe (graines fixes) : deux exécutions donnent exactement le même son.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfilt, sosfiltfilt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chrono  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
SR = 48000
TARGET_LUFS = -14.0
CEILING_DBTP = -1.6          # marge de 0,1 dB sous l'exigence de −1,5 dBFS
GAP_TARGET_DB = 20.0         # musique ≈ 20 dB sous la voix pendant la parole (minimum exigé : 15 dB)
FX_GAP_DB = 16.0       # bruitages : ≥ 12 dB sous la voix pendant la parole (cible 16 dB : le murmure de foule est continu)
RISE_DB = 12.0         # remontée de la musique dans les silences


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


def bp(x, lo, hi, order=4):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def lp(x, f, order=4):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def hp(x, f, order=4):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


def reverb_ir(rt60: float, seed: int, bright: float = 5000) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(rt60 * SR)
    t = np.arange(n) / SR
    env = np.exp(-6.9 * t / rt60)
    ir = np.stack([lp(rng.normal(0, 1, n), bright) * env for _ in range(2)], axis=1)
    ir[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))[:, None]
    return ir / np.sqrt((ir ** 2).sum(axis=0, keepdims=True))


def convolve_st(mono: np.ndarray, ir: np.ndarray) -> np.ndarray:
    n = len(mono) + len(ir) - 1
    nfft = 1 << (n - 1).bit_length()
    X = np.fft.rfft(mono, nfft)
    out = np.stack([np.fft.irfft(X * np.fft.rfft(ir[:, c], nfft), nfft)[: len(mono)] for c in range(2)], axis=1)
    return out


def place(buf: np.ndarray, sig: np.ndarray, t: float, gain=1.0):
    i = int(round(t * SR))
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


# ------------------------------------------------------------------ musique

def saw_additive(freq: float, n: int, harmonics=18, phase=0.0) -> np.ndarray:
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, harmonics + 1):
        if freq * k > 9000:
            break
        out += np.sin(2 * np.pi * freq * k * t + phase * k) / k
    return out


def bell(freq: float, dur=3.2, seed=0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    mod = 2.0 * np.exp(-t * 2.2) * np.sin(2 * np.pi * freq * 3.5 * t)
    car = np.sin(2 * np.pi * freq * t + mod) * np.exp(-t * 1.6)
    car += 0.25 * np.sin(2 * np.pi * freq * 2.01 * t) * np.exp(-t * 3.0)
    att = np.minimum(1, t / 0.004)
    return car * att


def pluck(freq: float, dur=1.4, seed=0) -> np.ndarray:
    """Karplus-Strong : pizzicato discret."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    period = int(SR / freq)
    buf = rng.uniform(-1, 1, period)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % period]
        buf[i % period] = 0.5 * (buf[i % period] + buf[(i + 1) % period]) * 0.994
    return lp(out, 2200)


def sub_hit(dur=1.2) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 62 * np.exp(-t * 2.5) + 38
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 3.2) * np.minimum(1, t / 0.008)


def music(tl: dict) -> np.ndarray:
    """Musique pilotée par les repères de plans.json (« musique ») : aucun numéro de plan codé en dur."""
    D = tl["duree"]
    n = int(round(D * SR))
    t = np.arange(n) / SR
    P = {p["id"]: p for p in tl["plans"]}
    M = tl["musique"]
    bt, pz = M["battement"], M["pizzicato"]
    t_accel = P[bt["accelere"]]["debut"]
    left = np.zeros(n)
    right = np.zeros(n)

    # 1) Bourdon : ré mineur, qui se résout en ré majeur (repère « resolution »), puis revient vers l'ouverture (boucle).
    t_resolve = P[M["resolution"]]["debut"]
    t_back = P[M["boucle"]]["debut"] + 1.2
    chord_min = [73.42, 110.0, 146.83, 174.61]   # ré2 la2 ré3 fa3
    chord_maj = [73.42, 110.0, 146.83, 185.00]   # ré2 la2 ré3 fa#3
    pad = np.zeros(n)
    for i, (fm, fM) in enumerate(zip(chord_min, chord_maj)):
        voice = saw_additive(fm * (1 + 0.0015 * (i - 1.5)), n, phase=i)
        if fm != fM:
            alt = saw_additive(fM, n, phase=i)
            xf = np.clip((t - t_resolve) / 1.0, 0, 1) * (1 - np.clip((t - t_back) / 1.5, 0, 1))
            voice = voice * (1 - xf) + alt * xf
        pad += voice * (0.9 if i < 2 else 0.6)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t)
    pad = lp(pad * (0.75 + 0.25 * lfo), 520) + 0.25 * lp(pad, 1400) * np.clip((t - t_accel) / 6, 0, 1)
    pad_env = 0.55 + 0.45 * np.clip((t - t_accel) / max(1.0, t_resolve - t_accel), 0, 1)
    pad_env *= np.clip(t / 0.25, 0, 1)
    left += pad * pad_env * 0.9
    right += np.roll(pad, int(0.011 * SR)) * pad_env * 0.9

    # 2) Battement grave : l'enquête, qui s'accélère au retournement.
    beat_t = P[bt["debut"]]["debut"]
    while beat_t < P[bt["fin"]]["debut"] - 0.2:
        period = 1.0 if beat_t < t_accel else 0.75
        s = sub_hit(0.6) * 0.55
        place(left, s, beat_t)
        place(right, s, beat_t)
        beat_t += period

    # 3) Pizzicato en arpège (ré mineur), très discret, sur l'enquête.
    notes = [146.83, 174.61, 220.0, 293.66, 220.0, 174.61]
    pt = P[pz["debut"]]["debut"]
    k = 0
    while pt < P[pz["fin"]]["fin"] - 0.3:
        pl = pluck(notes[k % len(notes)], 1.2, seed=k) * 0.22
        pan = 0.35 if k % 2 else -0.35
        place(left, pl * (1 - pan) / 1.2, pt)
        place(right, pl * (1 + pan) / 1.2, pt)
        pt += 0.375 if pt > t_accel else 0.5
        k += 1

    # 4) Cloches sur les révélations (clé « cloche » des plans), coup sourd (clé « coup »).
    for p in tl["plans"]:
        if "cloche" in p:
            b = bell(p["cloche"]["note"], 3.4) * 0.28
            place(left, b * 0.9, p["cloche"]["t"])
            place(right, b * 1.1, p["cloche"]["t"] + 0.007)
        if "coup" in p:
            s = sub_hit(1.6) * 0.9
            place(left, s, p["coup"]["t"])
            place(right, s, p["coup"]["t"])

    st = np.stack([left, right], axis=1)
    st = convolve_st(st.mean(axis=1), reverb_ir(2.6, 5, 3800)) * 0.35 + st
    tail = np.clip((D - t) / 0.6, 0, 1)[:, None]  # extinction douce pour la boucle
    return st * (0.4 + 0.6 * tail)


# ------------------------------------------------------------------ bruitages

def footsteps(times, rt60, seed, level=1.0, stone=True) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int((max(times) + rt60 + 0.5) * SR)
    dry = np.zeros(n)
    for i, ft in enumerate(times):
        m = int(0.09 * SR)
        tt = np.arange(m) / SR
        click = bp(rng.normal(0, 1, m), 900 if stone else 300, 5200 if stone else 2500) * np.exp(-tt * 70)
        thump = np.sin(2 * np.pi * 95 * tt) * np.exp(-tt * 45) * 0.6
        place(dry, (click * 0.8 + thump) * (0.8 + 0.2 * rng.random()), ft)
    wet = convolve_st(dry, reverb_ir(rt60, seed + 1, 4500))
    return (np.stack([dry, dry], axis=1) * 0.5 + wet * 0.8) * level


def door_clank(seed=3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(2.4 * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for f, d, a in [(196, 2.0, 1.0), (311, 2.6, 0.7), (523, 3.4, 0.5), (877, 4.8, 0.35), (1340, 6.0, 0.25)]:
        s += a * np.sin(2 * np.pi * f * t + rng.random() * 6) * np.exp(-t * d)
    s += bp(rng.normal(0, 1, n), 300, 4000) * np.exp(-t * 40) * 1.5
    s *= np.minimum(1, t / 0.002)
    return convolve_st(s, reverb_ir(1.8, seed, 3500)) * 0.6 + np.stack([s, s], axis=1) * 0.5


def glass_tink(seed=4) -> np.ndarray:
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d, a in [(2960, 4.5, 1.0), (4410, 6.0, 0.6), (6280, 8.0, 0.4)])
    s *= np.minimum(1, t / 0.001)
    return convolve_st(s, reverb_ir(1.2, seed, 7000)) * 0.4 + np.stack([s, s], axis=1) * 0.6


def drawer(seed=6) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    env = np.clip(t / 0.08, 0, 1) * np.clip((0.5 - t) / 0.12, 0, 1)
    s = bp(rng.normal(0, 1, n), 350, 2600) * env * 0.7
    s += np.sin(2 * np.pi * 70 * t) * env * 0.3
    knock = np.zeros(n)
    m = int(0.06 * SR)
    knock[int(0.5 * SR):int(0.5 * SR) + m] = bp(rng.normal(0, 1, m), 200, 1800) * np.exp(-np.arange(m) / SR * 60)
    s += knock * 1.4
    return convolve_st(s, reverb_ir(0.6, seed, 4000)) * 0.4 + np.stack([s, s], axis=1) * 0.6


def room_tone(n: int, seed=8) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = lp(rng.normal(0, 1, (n, 2)).T, 900).T
    return x * 0.6


def shutter(seed=31) -> np.ndarray:
    """Déclic d'obturateur mécanique : deux claquements brefs."""
    rng = np.random.default_rng(seed)
    n = int(0.6 * SR)
    s = np.zeros(n)
    for t0, dur, a in [(0.0, 0.006, 1.0), (0.07, 0.012, 0.7)]:
        m = int(dur * SR)
        s[int(t0 * SR):int(t0 * SR) + m] += bp(rng.normal(0, 1, m), 1800, 7000) * np.exp(-np.arange(m) / SR * 300) * a
    return convolve_st(s, reverb_ir(0.5, seed, 6000)) * 0.3 + np.stack([s, s], axis=1) * 0.7


def murmur(dur: float, seed=33) -> np.ndarray:
    """Murmure de foule lointain : voix inintelligibles (bruit filtré, enveloppes syllabiques aléatoires)."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for v in range(10):
        f0 = rng.uniform(3.5, 6.0)
        env = np.clip(np.sin(2 * np.pi * f0 * t + rng.uniform(0, 6)) + rng.uniform(-0.2, 0.4), 0, 1) ** 1.5
        env *= np.clip(np.sin(2 * np.pi * rng.uniform(0.15, 0.4) * t + rng.uniform(0, 6)) + 0.6, 0, 1)
        x = bp(rng.normal(0, 1, n), rng.uniform(250, 450), rng.uniform(1800, 2800)) * env
        pan = rng.uniform(-0.7, 0.7)
        out[:, 0] += x * (1 - pan)
        out[:, 1] += x * (1 + pan)
    fade = np.clip(t / 0.4, 0, 1) * np.clip((dur - t) / 0.5, 0, 1)
    wet = convolve_st(out.mean(axis=1), reverb_ir(1.8, seed, 3000))[:n]
    return (out * 0.5 + wet * 0.8) * fade[:, None] * 0.25


def sfx(tl: dict) -> np.ndarray:
    """Bruitages pilotés par la clé « bruitage » de chaque plan (discrets, justifiés par l'image)."""
    D = tl["duree"]
    n = int(round(D * SR))
    out = np.zeros((n, 2))
    for p in tl["plans"]:
        kind, t0, t1 = p.get("bruitage"), p["debut"], p["fin"]
        if kind == "salle":       # salle vide : souffle + trois pas lointains (réverbération longue)
            rt = room_tone(int((t1 - t0) * SR) + SR)
            k = np.arange(len(rt)) / SR
            fade = np.clip(k / 0.1, 0, 1) * np.clip((t1 - t0 + 0.6 - k) / 0.6, 0, 1)
            place(out, rt * fade[:, None] * 0.12, t0)
            place(out, footsteps([0.35, 0.95, 1.55], 2.4, 11, level=0.18), t0)
        elif kind == "porte":
            place(out, door_clank(), t0, 0.32)
        elif kind == "verre":
            place(out, glass_tink(), p.get("revele", {}).get("t", t0), 0.22)
        elif kind == "tiroir":
            place(out, drawer(), t0 + 0.05, 0.35)
        elif kind == "pas":
            place(out, footsteps([0, 0.52, 1.04, 1.56, 2.08], 1.4, 21, level=0.32), t0 + 0.2)
        elif kind == "declic":
            place(out, shutter(), t0 + 0.35, 0.5)
        elif kind == "murmure":
            place(out, murmur(t1 - t0 + 0.4), t0)
    return out


# ------------------------------------------------------------------ mixage et mesures

def compress(x: np.ndarray, thresh_db=-22, ratio=3.0, att=0.004, rel=0.08) -> np.ndarray:
    env = np.abs(x)
    a_att, a_rel = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
    out = np.empty_like(env)
    e = 0.0
    for i, v in enumerate(env):
        c = a_att if v > e else a_rel
        e = c * e + (1 - c) * v
        out[i] = e
    lvl = db(out)
    gr = np.where(lvl > thresh_db, (thresh_db - lvl) * (1 - 1 / ratio), 0.0)
    return x * 10 ** (gr / 20)


def speech_mask(voice: np.ndarray, tl: dict) -> np.ndarray:
    n = len(voice)
    m = np.zeros(n, bool)
    for p in tl["phrases"]:
        m[int(p["debut"] * SR):int(p["fin"] * SR)] = True
    return m


def smooth_gain(target_db: np.ndarray, att=0.12, rel=0.45) -> np.ndarray:
    out = np.empty_like(target_db)
    g = target_db[0]
    a_down, a_up = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
    for i, v in enumerate(target_db):
        c = a_down if v < g else a_up
        g = c * g + (1 - c) * v
        out[i] = g
    return out


def true_peak_db(x: np.ndarray) -> float:
    up = resample_poly(x, 4, 1, axis=0)
    return float(db(np.abs(up).max()))


def limiter_gain(x: np.ndarray, ceiling_db: float) -> np.ndarray:
    """Gain de limitation (anticipation 3 ms, relâchement 80 ms), appliqué identiquement à toutes les pistes."""
    up = np.abs(resample_poly(x, 4, 1, axis=0)).max(axis=1)
    peak = up.reshape(-1, 4).max(axis=1)[: len(x)]
    if len(peak) < len(x):
        peak = np.pad(peak, (0, len(x) - len(peak)))
    ceil = 10 ** (ceiling_db / 20)
    need = np.minimum(1.0, ceil / np.maximum(peak, 1e-9))
    look = int(0.003 * SR)
    from numpy.lib.stride_tricks import sliding_window_view
    padded = np.pad(need, (0, look), constant_values=1.0)
    need = sliding_window_view(padded, look + 1).min(axis=1)
    g = np.empty_like(need)
    cur = 1.0
    a_rel = np.exp(-1 / (0.08 * SR))
    for i, v in enumerate(need):
        cur = v if v < cur else a_rel * cur + (1 - a_rel) * v
        g[i] = cur
    return g


def main() -> None:
    tl = chrono.load()
    D = tl["duree"]
    n = int(round(D * SR))
    meter = pyln.Meter(SR)

    v, sr = sf.read(BUILD / "voix.wav", dtype="float64")
    assert sr == SR
    v = np.pad(v, (0, max(0, n - len(v))))[:n]
    v = hp(v, 75)
    v = compress(v)
    mask = speech_mask(v, tl)
    voice = np.stack([v, v], axis=1)

    mus = music(tl)
    fx = sfx(tl)

    # Ducking : musique à −GAP_TARGET_DB sous la voix pendant la parole, +RISE_DB dans les silences.
    v_lufs = meter.integrated_loudness(voice[mask])
    m_lufs = meter.integrated_loudness(mus[mask])
    base_gain_db = (v_lufs - GAP_TARGET_DB) - m_lufs
    hang = np.convolve(mask.astype(float), np.ones(int(0.12 * SR)), "same") > 0  # pas de remontée dans les micro-pauses
    target = np.where(hang, base_gain_db, base_gain_db + RISE_DB)
    # Sidechain : pendant la parole, la musique reste à ≥ GAP_TARGET_DB sous le niveau court terme réel de la voix
    # (évite qu'un coup de cloche ou une syllabe faible ne réduise l'écart sous 15 dB).
    def env_db(x, win=0.3):
        k = np.ones(int(win * SR)) / int(win * SR)
        return 10 * np.log10(np.convolve((x ** 2).mean(axis=1) if x.ndim > 1 else x ** 2, k, "same") + 1e-12)
    v_env = env_db(voice)
    m_env = env_db(mus) + base_gain_db
    cap = (v_env - GAP_TARGET_DB - 3.5) - m_env
    side = np.where(hang, np.minimum(0.0, cap), 0.0)
    gcurve = smooth_gain(target + np.maximum(side, -24.0), att=0.05, rel=0.22)
    mus_d = mus * 10 ** (gcurve / 20)[:, None]
    # Recalage fin : on règle la musique au plus fort possible en respectant les deux critères à la fois —
    # écart intégré ≥ GAP_TARGET_DB et écart ≥ 15,5 dB sur chaque fenêtre de 400 ms de parole.
    def active_windows(v):
        """Fenêtres de 400 ms où la voix parle vraiment : les pauses dramatiques à l'intérieur d'une phrase
        (fréquentes avec la voix Gemini) ne doivent pas fausser l'écart voix / musique."""
        win = int(0.4 * SR)
        idx = [i for i in range(0, n - win, win // 2) if mask[i:i + win].mean() > 0.9]
        lv = {i: db(np.sqrt(np.mean(v[i:i + win] ** 2))) for i in idx}
        ref = np.median(list(lv.values()))
        return [i for i in idx if lv[i] > ref - 20], win

    def window_min_gap(m):
        idx, win = active_windows(voice)
        return min(db(np.sqrt(np.mean(voice[i:i + win] ** 2))) - db(np.sqrt(np.mean(m[i:i + win] ** 2))) for i in idx)
    gap = meter.integrated_loudness(voice[mask]) - meter.integrated_loudness(mus_d[mask])
    wmin = window_min_gap(mus_d)
    print(f"avant recalage : écart intégré {gap:.2f} dB, pire fenêtre {wmin:.2f} dB", file=sys.stderr)
    mus_d *= 10 ** (min(gap - GAP_TARGET_DB, wmin - 15.5) / 20)
    fx_lufs = meter.integrated_loudness(fx[np.abs(fx).max(axis=1) > 1e-4]) if np.abs(fx).max() > 0 else -70
    fx = fx * 10 ** (((v_lufs - 10) - fx_lufs) / 20)
    # Bruitages discrets : pendant la parole, chaque bruitage reste ≥ FX_GAP_DB sous la voix (ex. la porte de P05,
    # qui tombe sur « Il passe… »). Dans les silences, ils gardent leur niveau.
    fx_cap = (v_env - FX_GAP_DB - 2.0) - env_db(fx, 0.2)
    fx_side = np.where(hang, np.clip(fx_cap, -30.0, 0.0), 0.0)
    fx = fx * 10 ** (smooth_gain(fx_side, att=0.01, rel=0.25) / 20)[:, None]

    mix = voice + mus_d + fx
    g = 10 ** ((TARGET_LUFS - meter.integrated_loudness(mix)) / 20)
    stems = {"voix": voice * g, "musique": mus_d * g, "bruitages": fx * g}
    mix = sum(stems.values())
    lim = limiter_gain(mix, CEILING_DBTP)
    stems = {k: s * lim[:, None] for k, s in stems.items()}
    mix = sum(stems.values())
    # Second passage : la limitation a pu abaisser très légèrement la loudness ; on ré-ajuste puis on relimite.
    g2 = 10 ** ((TARGET_LUFS - meter.integrated_loudness(mix)) / 20)
    stems = {k: s * g2 for k, s in stems.items()}
    mix = sum(stems.values())
    lim = limiter_gain(mix, CEILING_DBTP)
    stems = {k: s * lim[:, None] for k, s in stems.items()}
    mix = sum(stems.values())

    (BUILD / "stems").mkdir(parents=True, exist_ok=True)
    for k, s in stems.items():
        sf.write(BUILD / f"stems/{k}.wav", s, SR, subtype="PCM_24")
    sf.write(BUILD / "mix_master.wav", mix, SR, subtype="PCM_24")

    pauses = ~np.convolve(mask.astype(float), np.ones(int(0.25 * SR)), "same").astype(bool)
    res = {
        "duree_s": round(n / SR, 3),
        "loudness_integree_lufs": round(meter.integrated_loudness(mix), 2),
        "crete_vraie_dbtp": round(true_peak_db(mix), 2),
        "voix_pendant_parole_lufs": round(meter.integrated_loudness(stems["voix"][mask]), 2),
        "musique_pendant_parole_lufs": round(meter.integrated_loudness(stems["musique"][mask]), 2),
        "musique_dans_les_silences_lufs": round(meter.integrated_loudness(stems["musique"][pauses]), 2) if pauses.sum() > SR * 0.5 else None,
    }
    res["ecart_voix_musique_db"] = round(res["voix_pendant_parole_lufs"] - res["musique_pendant_parole_lufs"], 2)
    # Écart à court terme (fenêtres de 400 ms pendant la parole) : on garde le pire cas réaliste (5e centile).
    win = int(0.4 * SR)
    diffs = []
    for i in active_windows(stems["voix"])[0]:
        vv = np.sqrt(np.mean(stems["voix"][i:i + win] ** 2))
        mm = np.sqrt(np.mean(stems["musique"][i:i + win] ** 2))
        diffs.append(db(vv) - db(mm))
    diffs = np.array(diffs)
    res["ecart_court_terme_db"] = {"median": round(float(np.median(diffs)), 1), "p5": round(float(np.percentile(diffs, 5)), 1),
                                   "min": round(float(diffs.min()), 1), "fenetres": int(len(diffs)),
                                   "part_fenetres_sous_15db": round(float((diffs < 15).mean()) * 100, 1)}
    fxd = []
    vref = np.median([db(np.sqrt(np.mean(stems["voix"][i:i + win] ** 2))) for i in range(0, n - win, win) if mask[i:i + win].mean() > 0.9])
    for i in range(0, n - win, win // 4):
        ff = np.sqrt(np.mean(stems["bruitages"][i:i + win] ** 2))
        vv = db(np.sqrt(np.mean(stems["voix"][i:i + win] ** 2)))
        if mask[i:i + win].mean() > 0.5 and db(ff) > -60 and vv > vref - 20:   # seulement quand la voix parle vraiment
            fxd.append(vv - db(ff))
    res["ecart_voix_bruitages_db"] = {"median": round(float(np.median(fxd)), 1), "min": round(float(np.min(fxd)), 1),
                                      "fenetres": len(fxd)} if fxd else None
    (BUILD / "audio_mesures.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
