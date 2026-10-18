#!/usr/bin/env python3
"""Voix off : synthèse phrase par phrase, assemblage, chronologie.

Moteur livré : Gemini TTS (voix Google, `scripts/voix_gemini.mjs`, clé GEMINI_API_KEY ou GOOGLE_API_KEY).
Moteur de brouillon : Kokoro (local), seulement sur demande explicite (`--brouillon-kokoro`) pour caler un
montage en attendant la clé. Il n'est jamais utilisé en repli silencieux.

Entrée  : scripts/script.json
Sorties : build/voix/phrase_XX.wav, build/voix.wav (48 kHz mono), build/chronologie.json

Aucun des deux moteurs ne fournit d'horodatage par mot : chaque phrase est donc synthétisée seule
(ses bornes sont exactes), puis ses mots sont répartis au prorata de leurs phonèmes et recalés sur
les silences réellement présents dans le signal (virgules, deux-points).
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from kokoro_onnx.tokenizer import Tokenizer

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
TTS_CACHE = Path(os.environ.get("KOKORO_DIR", Path.home() / ".cache/hyperframes/tts"))
SR_OUT = 48000


def load_kokoro():
    from kokoro_onnx import Kokoro
    model = TTS_CACHE / "models/kokoro-v1.0.onnx"
    voices = TTS_CACHE / "voices/voices-v1.0.bin"
    if not model.exists():
        sys.exit(f"Modèle Kokoro absent ({model}). Lancer une fois : npx hyperframes tts \"test\" -v ff_siwis")
    return Kokoro(str(model), str(voices))


def resample(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    """Rééchantillonnage de qualité via ffmpeg (soxr)."""
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr_in), "-ac", "1", "-i", "pipe:0",
         "-af", f"aresample={sr_out}:resampler=soxr", "-f", "f32le", "pipe:1"],
        input=x.astype(np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).copy()


def trim(x: np.ndarray, sr: int, thresh_db: float = -45.0, keep: float = 0.02) -> np.ndarray:
    env = np.abs(x)
    th = 10 ** (thresh_db / 20) * max(1e-9, env.max())
    idx = np.where(env > th)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(keep * sr))
    b = min(len(x), idx[-1] + int(keep * sr))
    return x[a:b]


def phonemes_count(k: Tokenizer, word: str) -> int:
    w = re.sub(r"[^\wÀ-ÿ'’-]", "", word)
    if not w:
        return 0
    ph = k.phonemize(w, "fr-fr")
    return max(1, len(re.sub(r"[ˈˌː\s]", "", ph)))


def silent_gaps(x: np.ndarray, sr: int, min_len: float = 0.07) -> list[tuple[float, float]]:
    """Intervalles de silence internes (énergie < -38 dB du pic), en secondes."""
    hop = int(0.01 * sr)
    frames = len(x) // hop
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(frames)])
    th = rms.max() * 10 ** (-38 / 20)
    low = rms < th
    gaps, start = [], None
    for i, v in enumerate(low):
        if v and start is None:
            start = i
        if (not v or i == frames - 1) and start is not None:
            end = i if not v else i + 1
            if (end - start) * 0.01 >= min_len and start > 2 and end < frames - 2:
                gaps.append((start * 0.01, end * 0.01))
            start = None
    return gaps


def word_timings(k: Tokenizer, display: str, spoken: str, audio: np.ndarray, sr: int) -> list[dict]:
    words = display.split()
    spoken_words = spoken.split()
    if len(spoken_words) != len(words):
        spoken_words = words  # même découpage requis ; sinon on retombe sur le texte affiché
    weights = [phonemes_count(k, w) for w in spoken_words]
    dur = len(audio) / sr
    gaps = silent_gaps(audio, sr)
    # Points d'ancrage : fin des mots suivis d'une ponctuation forte ↔ centre du silence le plus proche.
    total = sum(weights)
    cum = np.cumsum([0] + weights) / total
    anchors = {0: 0.0, len(words): dur}
    free = list(gaps)          # chaque silence ne sert qu'une fois, dans l'ordre de la phrase
    last = 0.0
    for i, w in enumerate(words[:-1]):
        if re.search(r"[,;:…]$", w) or (i + 1 < len(words) and words[i + 1] in (":", ";")):
            guess = cum[i + 1] * dur
            cands = [g for g in free if g[0] > last]
            if cands:
                g = min(cands, key=lambda g: abs((g[0] + g[1]) / 2 - guess))
                if abs((g[0] + g[1]) / 2 - guess) < 0.6:
                    anchors[i + 1] = g[1]
                    last = g[1]
                    free.remove(g)
    keys = sorted(anchors)
    times = [0.0] * (len(words) + 1)
    for a, b in zip(keys, keys[1:]):
        seg_w = weights[a:b]
        s = sum(seg_w) or 1
        t0, t1 = anchors[a], anchors[b]
        acc = 0
        for j in range(a, b + 1):
            times[j] = t0 + (t1 - t0) * acc / s
            if j < b:
                acc += weights[j]
    return [{"mot": w, "debut": round(times[i], 3), "fin": round(times[i + 1], 3)} for i, w in enumerate(words)]


def gemini_audio(cfg: dict) -> dict[int, tuple[np.ndarray, int]]:
    """Synthétise toutes les phrases avec Gemini (cache par phrase) et renvoie {id: (audio, sr)}."""
    v = cfg["voix"]
    work = BUILD / "voix_gemini"
    work.mkdir(parents=True, exist_ok=True)
    jobs = [{"id": ph["id"], "texte": ph["texte"],
             "style": " ".join(x for x in (v.get("style"), ph.get("style")) if x),
             "wav": str(work / f"phrase_{ph['id']:02d}.wav")} for ph in cfg["phrases"]]
    (work / "travaux.json").write_text(json.dumps({"modele": v["modele"], "voix": v["voix"], "jobs": jobs},
                                                  ensure_ascii=False, indent=1))
    r = subprocess.run(["node", str(ROOT / "scripts/voix_gemini.mjs"), str(work / "travaux.json")])
    if r.returncode != 0:
        sys.exit("Synthèse Gemini incomplète : voir les messages ci-dessus (aucun repli automatique sur une autre voix).")
    out = {}
    for j in jobs:
        a, sr = sf.read(j["wav"], dtype="float32", always_2d=True)
        out[j["id"]] = (a.mean(axis=1), sr)
    return out


def level(x: np.ndarray, sr: int, target_lufs: float = -20.0) -> np.ndarray:
    """Même loudness pour chaque phrase : pas de saut de niveau d'une phrase à l'autre."""
    m = pyln.Meter(sr, block_size=min(0.4, len(x) / sr * 0.9))
    lufs = m.integrated_loudness(x.astype(np.float64))
    return x * 10 ** ((target_lufs - lufs) / 20) if np.isfinite(lufs) else x


def main() -> None:
    cfg = json.loads((ROOT / "scripts/script.json").read_text())
    vcfg = cfg["voix"]
    brouillon = "--brouillon-kokoro" in sys.argv
    moteur = "kokoro" if brouillon else vcfg["moteur"]
    tok = Tokenizer()
    if moteur == "gemini":
        raw = gemini_audio(cfg)
        ident = {"moteur": "gemini", "modele": vcfg["modele"], "voix": vcfg["voix"], "brouillon": False}
    elif moteur == "kokoro":
        k, rk = load_kokoro(), vcfg.get("repli_kokoro", vcfg)
        raw = {}
        for ph in cfg["phrases"]:
            a, sr = k.create(ph.get("tts_kokoro", ph["texte"]), voice=rk["voix"], speed=rk.get("vitesse", 1.0), lang=rk["langue"])
            raw[ph["id"]] = (np.asarray(a, dtype=np.float32), sr)
        ident = {"moteur": "kokoro", "modele": "kokoro-v1.0", "voix": rk["voix"], "brouillon": True}
    else:
        sys.exit(f"Moteur de voix inconnu : {moteur}")
    (BUILD / "voix").mkdir(parents=True, exist_ok=True)
    pieces, chrono = [], []
    t = float(vcfg.get("debut_s", 0.2))
    pieces.append(np.zeros(int(t * SR_OUT), dtype=np.float32))
    for ph in cfg["phrases"]:
        spoken = ph["texte"]
        a, sr = raw[ph["id"]]
        audio = level(trim(resample(a, sr, SR_OUT), SR_OUT), SR_OUT)
        sf.write(BUILD / f"voix/phrase_{ph['id']:02d}.wav", audio, SR_OUT, subtype="PCM_24")
        d = len(audio) / SR_OUT
        words = word_timings(tok, ph["texte"], spoken, audio, SR_OUT)
        for w in words:
            w["debut"] = round(w["debut"] + t, 3)
            w["fin"] = round(w["fin"] + t, 3)
        chrono.append({
            "id": ph["id"], "role": ph["role"], "texte": ph["texte"],
            "phonemes": tok.phonemize(spoken, "fr-fr"),
            "debut": round(t, 3), "fin": round(t + d, 3), "duree": round(d, 3), "mots": words,
        })
        pieces.append(audio)
        pause = float(ph.get("pause", 0.3))
        pieces.append(np.zeros(int(pause * SR_OUT), dtype=np.float32))
        t += d + pause
    voice = np.concatenate(pieces)
    peak = np.abs(voice).max()
    voice = voice / peak * 10 ** (-3 / 20)  # crête provisoire à -3 dBFS ; le niveau final se règle au mixage
    sf.write(BUILD / "voix.wav", voice, SR_OUT, subtype="PCM_24")
    syll = sum(len(re.findall(r"[aeiouyɛɔøœəɑ]", c["phonemes"])) for c in chrono)
    speech = sum(c["duree"] for c in chrono)
    out = {
        **ident,
        "voix_fin": round(t, 3), "duree_parole": round(speech, 3), "mots": sum(len(c["texte"].split()) for c in chrono),
        "syllabes_estimees": syll, "debit_syll_par_s": round(syll / speech, 2), "phrases": chrono,
    }
    (BUILD / "chronologie.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    tag = " — BROUILLON (voix Kokoro, à ne pas livrer)" if ident["brouillon"] else ""
    print(f"voix {ident['moteur']}/{ident['voix']}{tag}: {out['mots']} mots · parole {speech:.2f}s · fin voix {t:.2f}s · "
          f"~{out['debit_syll_par_s']} syll/s")
    for c in chrono:
        print(f"  {c['id']:2d} {c['debut']:6.2f}–{c['fin']:6.2f}  {c['texte']}")


if __name__ == "__main__":
    main()
