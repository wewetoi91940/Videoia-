#!/usr/bin/env python3
"""Audio : nappe musicale synthétisée (libre de droits), mixage sous la voix, mastering, mesures.

Entrées  : build/voix.wav, build/chronologie.json, build/plans_calcules.json, scripts/script.json
Sorties  : build/stems/{voix,musique,bruitages}.wav (leur somme = le master), build/mix_master.wav
           (−14 LUFS intégrés, crête vraie ≤ −1,5 dBTP), build/audio_mesures.json
Pas de bruitages d'émeute ni de foule : rien qui ferait croire à un enregistrement de la journée.
Seul « bruitage » : un tic d'horloge discret sur les cartons d'heure. Tout est déterministe (graines fixes).
Fonctions de filtrage, compression, limitation reprises de la chaîne « joconde-1911 ».
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from numpy.lib.stride_tricks import sliding_window_view
from scipy.ndimage import uniform_filter1d
from scipy.signal import butter, resample_poly, sosfilt

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
SR = 48000
TARGET_LUFS = -14.0
CEILING_DBTP = -1.6
GAP_TARGET_DB = 21.0         # musique ≈ 21 dB sous la voix pendant la parole (minimum exigé : 15 dB)
FX_GAP_DB = 16.0
RISE_DB = 9.0                # remontée de la musique dans les silences (pas de « nappe dramatique »)

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



def sub_hit(dur=1.2) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 62 * np.exp(-t * 2.5) + 38
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 3.2) * np.minimum(1, t / 0.008)



BLK = 48   # bloc de contrôle de 1 ms : les enveloppes et les gains sont calculés par bloc puis interpolés
           # (8 min de son = 23 millions d'échantillons : une boucle Python par échantillon serait trop lente)


def _blocs(x: np.ndarray, fn=np.max) -> np.ndarray:
    n = (len(x) + BLK - 1) // BLK * BLK
    return fn(np.pad(x, (0, n - len(x))).reshape(-1, BLK), axis=1)


def _vers_echantillons(gb: np.ndarray, n: int) -> np.ndarray:
    return np.interp(np.arange(n), (np.arange(len(gb)) + 0.5) * BLK, gb)


def _suiveur(v: np.ndarray, t_baisse: float, t_hausse: float) -> np.ndarray:
    """Suiveur d'enveloppe à deux constantes de temps, par bloc."""
    a_b, a_h = np.exp(-BLK / (t_baisse * SR)), np.exp(-BLK / (t_hausse * SR))
    out = np.empty_like(v)
    g = v[0]
    for i, x in enumerate(v):
        c = a_b if x < g else a_h
        g = c * g + (1 - c) * x
        out[i] = g
    return out


def moyenne_glissante(x: np.ndarray, taille: int) -> np.ndarray:
    return uniform_filter1d(x.astype(np.float64), taille, mode="constant")


def compress(x: np.ndarray, thresh_db=-22, ratio=3.0, att=0.004, rel=0.08) -> np.ndarray:
    env = -_suiveur(-_blocs(np.abs(x)), rel, att)          # attaque rapide vers le haut, relâchement lent
    lvl = db(env)
    gr = np.where(lvl > thresh_db, (thresh_db - lvl) * (1 - 1 / ratio), 0.0)
    return x * 10 ** (_vers_echantillons(gr, len(x)) / 20)


def speech_mask(voice: np.ndarray, tl: dict) -> np.ndarray:
    n = len(voice)
    m = np.zeros(n, bool)
    for p in tl["phrases"]:
        m[int(p["debut"] * SR):int(p["fin"] * SR)] = True
    return m


def smooth_gain(target_db: np.ndarray, att=0.12, rel=0.45) -> np.ndarray:
    return _vers_echantillons(_suiveur(_blocs(target_db, np.mean), att, rel), len(target_db))


def _crete_vraie_blocs(x: np.ndarray) -> np.ndarray:
    """Crête vraie (suréchantillonnage ×4) par bloc de 1 ms, calculée par morceaux pour tenir en mémoire."""
    n = len(x)
    nb = (n + BLK - 1) // BLK
    out = np.zeros(nb)
    pas = BLK * 20000
    for a in range(0, n, pas):
        b = min(n, a + pas)
        m0, m1 = min(a, 64), min(n - b, 64)
        up = np.abs(resample_poly(x[a - m0:b + m1], 4, 1, axis=0))
        up = up.max(axis=1) if up.ndim > 1 else up
        up = up[4 * m0: 4 * m0 + 4 * (b - a)]
        k = (len(up) + 4 * BLK - 1) // (4 * BLK)
        out[a // BLK: a // BLK + k] = np.pad(up, (0, k * 4 * BLK - len(up))).reshape(k, -1).max(axis=1)
    return out


def true_peak_db(x: np.ndarray) -> float:
    return float(db(_crete_vraie_blocs(x).max()))


def limiter_gain(x: np.ndarray, ceiling_db: float) -> np.ndarray:
    """Gain de limitation (anticipation 3 ms, relâchement 80 ms), appliqué identiquement à toutes les pistes.
    Le gain d'un échantillon ne dépasse jamais celui de son bloc : la crête reste sous le plafond."""
    need = np.minimum(1.0, 10 ** (ceiling_db / 20) / np.maximum(_crete_vraie_blocs(x), 1e-9))
    look = 3
    need = sliding_window_view(np.pad(need, (0, look), constant_values=1.0), look + 1).min(axis=1)
    g = np.empty_like(need)
    cur = 1.0
    a_rel = np.exp(-BLK / (0.08 * SR))
    for i, v in enumerate(need):
        cur = v if v < cur else a_rel * cur + (1 - a_rel) * v
        g[i] = cur
    n = len(x)
    return np.minimum(np.repeat(g, BLK)[:n], _vers_echantillons(g, n))


# ------------------------------------------------------------------ musique
NOTES = {"D1": 36.71, "F1": 43.65, "G1": 49.0, "A1": 55.0, "Bb1": 58.27, "C2": 65.41, "D2": 73.42, "E2": 82.41,
         "F2": 87.31, "G2": 98.0, "A2": 110.0, "Bb2": 116.54, "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61,
         "G3": 196.0, "A3": 220.0}
ACCORDS = {  # une couleur harmonique par ambiance de séquence ; tout reste dans ré mineur
    "ouverture": ["D2", "A2", "D3", "F3"], "contexte": ["Bb1", "F2", "D3", "F3"], "matin": ["G1", "D2", "G2", "Bb2"],
    "tension": ["D2", "A2", "D3", "E3"], "arret": ["A1", "E2", "A2", "C3"], "nuit": ["F1", "C2", "A2", "C3"],
    "apres": ["Bb1", "F2", "D3", "F3"], "chiffres": ["G1", "D2", "Bb2", "D3"], "fin": ["D2", "A2", "D3", "E3"],
}


SR_NAPPE = 4000   # la nappe est filtrée sous 480 Hz : synthèse à 4 kHz, puis suréchantillonnage ×12


def pad_voice(freqs: list[float], n: int, seed: int) -> np.ndarray:
    m = n // (SR // SR_NAPPE) + 1
    t = np.arange(m) / SR_NAPPE
    out = np.zeros(m)
    for i, f in enumerate(freqs):
        f = f * (1 + 0.0017 * (i - 1.5))
        for k in range(1, 15):
            if f * k > 1800:
                break
            out += np.sin(2 * np.pi * f * k * t + (seed + i) * k) / k * (0.9 if i < 2 else 0.55)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (0.05 + 0.01 * seed) * t + seed)
    out = sosfilt(butter(4, 480, "low", fs=SR_NAPPE, output="sos"), out * (0.8 + 0.2 * lfo))
    return resample_poly(out, SR // SR_NAPPE, 1)[:n]


def tick(seed=0) -> np.ndarray:
    """Tic d'horloge : clic boisé très court (bruit filtré, décroissance 25 ms), puis « tac » plus grave."""
    rng = np.random.default_rng(seed)
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    c = bp(rng.normal(0, 1, n), 1800, 5200) * np.exp(-t / 0.006)
    c += 0.6 * np.sin(2 * np.pi * 2300 * t) * np.exp(-t / 0.012)
    return c / np.abs(c).max()


def music(plans: list[dict], sequences: dict, chrono: dict, D: float) -> np.ndarray:
    n = int(round(D * SR))
    t = np.arange(n) / SR
    # 1) Nappe : un accord par séquence, enchaînés en fondus de 3 s, calés sur le début réel de chaque séquence.
    debuts = {}
    for p in chrono["phrases"]:
        debuts.setdefault(p["seq"], p["debut"])
    seqs = sorted(debuts)
    couches = {}
    for amb in sorted({sequences[s]["ambiance"] for s in seqs}):   # ordre fixe : graine de chaque nappe reproductible
        couches[amb] = pad_voice([NOTES[x] for x in ACCORDS[amb]], n, seed=len(couches))
    poids = {amb: np.zeros(n) for amb in couches}
    for k, s in enumerate(seqs):
        a = max(0.0, debuts[s] - 1.5) if k else 0.0
        b = debuts[seqs[k + 1]] - 1.5 if k + 1 < len(seqs) else D
        w = np.clip((t - a) / 3.0, 0, 1) * np.clip((b + 3.0 - t) / 3.0, 0, 1) if k else np.clip((b + 3.0 - t) / 3.0, 0, 1)
        poids[sequences[s]["ambiance"]] = np.maximum(poids[sequences[s]["ambiance"]], w)
    pad = sum(couches[a] * poids[a] for a in couches)
    pad *= np.clip(t / 2.0, 0, 1)
    left, right = pad.copy(), np.roll(pad, int(0.013 * SR))

    # 2) Pouls grave et lent sur les séquences marquées « pouls » (pas de crescendo spectaculaire).
    for k, s in enumerate(seqs):
        if not sequences[s].get("pouls"):
            continue
        a = debuts[s]
        b = debuts[seqs[k + 1]] - 0.8 if k + 1 < len(seqs) else D - 2
        bt = a
        while bt < b:
            h = sub_hit(0.7) * 0.42
            place(left, h, bt)
            place(right, h, bt)
            bt += 60 / 64

    # 3) Repères des plans : « impact » (coup sourd + cloche grave), « coupure » (silence musical de 1,3 s).
    gain = np.ones(n)
    for p in plans:
        cue = p.get("musique")
        if cue == "impact":
            h = sub_hit(1.6) * 0.8
            b_ = bell(NOTES["D3"], 3.0) * 0.16
            for buf, d in ((left, 0.0), (right, 0.006)):
                place(buf, h, p["debut"])
                place(buf, b_, p["debut"] + d)
        elif cue == "coupure":
            a, b = p["debut"] - 0.15, p["debut"] + 1.3
            gain = np.minimum(gain, np.clip(np.maximum((a - t) / 0.12, (t - b) / 0.6), 0, 1))
    st = np.stack([left, right], axis=1) * gain[:, None]
    st = convolve_st(st.mean(axis=1), reverb_ir(3.2, 7, 3200)) * 0.4 + st
    fin = np.clip((D - t) / 3.5, 0, 1)[:, None]
    return st * fin


def bruitages(plans: list[dict], D: float) -> np.ndarray:
    n = int(round(D * SR))
    fx = np.zeros((n, 2))
    for k, p in enumerate(plans):
        if p["type"] == "heure":
            for j, (dt, f) in enumerate(((0.0, 1.0), (0.5, 0.75))):
                c = tick(seed=k * 2 + j) * f
                if j:
                    c = lp(c, 1600)
                place(fx[:, 0], c * 0.9, p["debut"] + dt)
                place(fx[:, 1], c, p["debut"] + dt + 0.004)
    return fx


def mixer(v: np.ndarray, chrono: dict, plans: list[dict], sequences: dict, D: float, dossier: Path,
          avec_stems: bool = True) -> dict:
    """Mixe la voix v (mono, SR) avec la musique et les bruitages du montage `plans` (durée D) ;
    écrit dossier/mix_master.wav (et dossier/stems/) et renvoie les mesures. Sert aussi aux parties TikTok."""
    n = int(round(D * SR))
    meter = pyln.Meter(SR)
    v = np.pad(v, (0, max(0, n - len(v))))[:n]
    v = compress(hp(v, 75))
    mask = speech_mask(v, chrono)
    voice = np.stack([v, v], axis=1)
    mus = music(plans, sequences, chrono, D)
    fx = bruitages(plans, D)

    v_lufs = meter.integrated_loudness(voice[mask])
    m_lufs = meter.integrated_loudness(mus[mask])
    base_gain_db = (v_lufs - GAP_TARGET_DB) - m_lufs
    hang = moyenne_glissante(mask, int(0.12 * SR)) > 1e-6

    def env_db(x, win=0.3):
        return 10 * np.log10(moyenne_glissante((x ** 2).mean(axis=1) if x.ndim > 1 else x ** 2, int(win * SR)) + 1e-12)

    v_env = env_db(voice)
    m_env = env_db(mus) + base_gain_db
    cap = (v_env - GAP_TARGET_DB - 3.5) - m_env
    side = np.where(hang, np.minimum(0.0, cap), 0.0)
    target = np.where(hang, base_gain_db, base_gain_db + RISE_DB)
    gcurve = smooth_gain(target + np.maximum(side, -24.0), att=0.05, rel=0.35)
    mus_d = mus * 10 ** (gcurve / 20)[:, None]

    def active_windows(x):
        """Fenêtres de 400 ms où la voix parle vraiment (les pauses internes ne faussent pas la mesure)."""
        win = int(0.4 * SR)
        idx = [i for i in range(0, n - win, win // 2) if mask[i:i + win].mean() > 0.9]
        lv = {i: db(np.sqrt(np.mean(x[i:i + win] ** 2))) for i in idx}
        ref = np.median(list(lv.values()))
        return [i for i in idx if lv[i] > ref - 20], win

    def window_min_gap(m):
        idx, win = active_windows(voice)
        return min(db(np.sqrt(np.mean(voice[i:i + win] ** 2))) - db(np.sqrt(np.mean(m[i:i + win] ** 2))) for i in idx)

    gap = meter.integrated_loudness(voice[mask]) - meter.integrated_loudness(mus_d[mask])
    wmin = window_min_gap(mus_d)
    mus_d *= 10 ** (min(gap - GAP_TARGET_DB, wmin - 15.5) / 20)
    if np.abs(fx).max() > 0:
        actif = fx[np.abs(fx).max(axis=1) > 1e-4]
        if len(actif) <= meter.block_size * SR:   # trop court pour la mesure (une seule carte d'heure) : on le répète
            actif = np.tile(actif, (int(meter.block_size * SR) // len(actif) + 2, 1))
        fx_lufs = meter.integrated_loudness(actif)
        fx = fx * 10 ** (((v_lufs - 14) - fx_lufs) / 20)
        fx_cap = (v_env - FX_GAP_DB - 2.0) - env_db(fx, 0.2)
        fx = fx * 10 ** (smooth_gain(np.where(hang, np.clip(fx_cap, -30.0, 0.0), 0.0), att=0.01, rel=0.25) / 20)[:, None]

    mix = voice + mus_d + fx
    stems = {"voix": voice, "musique": mus_d, "bruitages": fx}
    for _ in range(2):   # gain global, limitation commune à toutes les pistes, puis ré-ajustement
        g = 10 ** ((TARGET_LUFS - meter.integrated_loudness(mix)) / 20)
        stems = {k: s * g for k, s in stems.items()}
        lim = limiter_gain(sum(stems.values()), CEILING_DBTP)
        stems = {k: s * lim[:, None] for k, s in stems.items()}
        mix = sum(stems.values())

    if avec_stems:
        (dossier / "stems").mkdir(parents=True, exist_ok=True)
        for k, s in stems.items():
            sf.write(dossier / f"stems/{k}.wav", s, SR, subtype="PCM_24")
    sf.write(dossier / "mix_master.wav", mix, SR, subtype="PCM_24")

    pauses = moyenne_glissante(mask, int(0.25 * SR)) < 1e-6
    res = {
        "duree_s": round(n / SR, 3),
        "loudness_integree_lufs": round(meter.integrated_loudness(mix), 2),
        "crete_vraie_dbtp": round(true_peak_db(mix), 2),
        "voix_pendant_parole_lufs": round(meter.integrated_loudness(stems["voix"][mask]), 2),
        "musique_pendant_parole_lufs": round(meter.integrated_loudness(stems["musique"][mask]), 2),
        "musique_dans_les_silences_lufs": round(meter.integrated_loudness(stems["musique"][pauses]), 2)
        if pauses.sum() > SR * 0.5 else None,
    }
    res["ecart_voix_musique_db"] = round(res["voix_pendant_parole_lufs"] - res["musique_pendant_parole_lufs"], 2)
    idx, win = active_windows(stems["voix"])
    diffs = np.array([db(np.sqrt(np.mean(stems["voix"][i:i + win] ** 2))) - db(np.sqrt(np.mean(stems["musique"][i:i + win] ** 2)))
                      for i in idx])
    res["ecart_court_terme_db"] = {"median": round(float(np.median(diffs)), 1), "p5": round(float(np.percentile(diffs, 5)), 1),
                                   "min": round(float(diffs.min()), 1), "fenetres": int(len(diffs))}
    return res


def main() -> None:
    chrono = json.loads((BUILD / "chronologie.json").read_text())
    calc = json.loads((BUILD / "plans_calcules.json").read_text())
    sequences = {s["n"]: s for s in json.loads((ROOT / "scripts/script.json").read_text())["sequences"]}
    v, sr = sf.read(BUILD / "voix.wav", dtype="float64")
    assert sr == SR
    res = mixer(v, chrono, calc["plans"], sequences, calc["duree"], BUILD)
    (BUILD / "audio_mesures.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
