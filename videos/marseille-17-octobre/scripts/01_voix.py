#!/usr/bin/env python3
"""Voix off du documentaire « Marseille, 17 octobre » : synthèse, assemblage, chronologie des mots.

Repris de la chaîne « joconde-1911 » ; ici les blocs Gemini suivent les séquences du film (`voix.blocs`).

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


def tempo(x: np.ndarray, sr: int, factor: float) -> np.ndarray:
    """Accélération sans changement de hauteur (ffmpeg atempo) : sert à resserrer l'accroche."""
    if abs(factor - 1.0) < 1e-3:
        return x
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0",
         "-af", f"atempo={factor}", "-f", "f32le", "pipe:1"],
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


def gemini_audio(cfg: dict, tok: Tokenizer) -> dict[int, tuple[np.ndarray, int]]:
    """Synthétise la voix avec Gemini par blocs de phrases (quota gratuit : quelques requêtes par jour et par modèle),
    puis redécoupe chaque bloc en phrases sur les silences réels. Renvoie {id: (audio, sr)}."""
    v = cfg["voix"]
    work = BUILD / "voix_gemini" / "blocs"
    work.mkdir(parents=True, exist_ok=True)
    phrases = cfg["phrases"]
    if "blocs" in v:   # un bloc = une ou plusieurs séquences entières : la voix garde son élan d'une phrase à l'autre
        blocs = [[ph for ph in phrases if ph["seq"] in groupe] for groupe in v["blocs"]]
    else:
        taille = int(v.get("phrases_par_bloc", 9))
        blocs = [phrases[i:i + taille] for i in range(0, len(phrases), taille)]
    if sum(len(b) for b in blocs) != len(phrases):
        sys.exit("voix.blocs ne couvre pas exactement toutes les phrases")
    jobs = [{"id": f"bloc{k + 1}", "texte": "\n\n".join(ph.get("dit", ph["texte"]) for ph in bl), "style": v.get("style", ""),
             "wav": str(work / f"bloc_{k + 1}.wav")} for k, bl in enumerate(blocs)]
    (BUILD / "voix_gemini" / "travaux.json").write_text(
        json.dumps({"modele": v["modele"], "voix": v["voix"], "jobs": jobs}, ensure_ascii=False, indent=1))
    r = subprocess.run(["node", str(ROOT / "scripts/voix_gemini.mjs"), str(BUILD / "voix_gemini" / "travaux.json")])
    if r.returncode != 0:
        sys.exit("Synthèse Gemini incomplète : voir les messages ci-dessus (aucun repli automatique sur une autre voix).")
    out = {}
    for j, bl in zip(jobs, blocs):
        a, sr = sf.read(j["wav"], dtype="float32", always_2d=True)
        a = a.mean(axis=1)
        # Bornes des phrases : alignement du texte sur la transcription Whisper du bloc (robuste aux longues pauses
        # que Gemini marque à l'intérieur des phrases, qui trompaient un découpage fondé sur les seuls silences).
        cuts = aligner(a, sr, [ph.get("dit", ph["texte"]) for ph in bl], transcrire(Path(j["wav"]), j["id"]))
        for ph, (t0, t1) in zip(bl, cuts):
            out[ph["id"]] = (a[int(t0 * sr):int(t1 * sr)], sr)
    return out


def _normaliser(texte: str) -> str:
    """Texte → lettres minuscules sans accents, nombres et heures écrits en toutes lettres (« 11h28 » → « onze heures vingt huit »)."""
    import unicodedata
    from num2words import num2words
    t = texte.lower().replace("’", "'")
    t = re.sub(r"(\d)\s*h\s*(\d{2})", r"\1 heures \2", t)
    t = re.sub(r"(\d)\s*h\b", r"\1 heures", t)
    t = re.sub(r"(\d)[\s\u202f\u00a0.](\d{3})\b", r"\1\2", t)        # 30 000 / 30.000 → 30000
    t = re.sub(r"\d+", lambda m: " " + num2words(int(m.group()), lang="fr") + " ", t)
    t = unicodedata.normalize("NFD", t)
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = re.sub(r"[^a-z]+", " ", t)
    return " ".join(t.split())


def transcrire(wav: Path, nom: str) -> list[dict]:
    """Mots horodatés du bloc (Whisper « small », français) via `hyperframes transcribe` ; mis en cache."""
    cache = BUILD / "transcription" / f"{nom}.json"
    cle = BUILD / "transcription" / f"{nom}.cle"
    signature = f"{wav.stat().st_size}-{wav.stat().st_mtime_ns}"
    if cache.exists() and cle.exists() and cle.read_text() == signature:
        return json.loads(cache.read_text())
    travail = BUILD / "transcription" / nom
    travail.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "NODE_USE_ENV_PROXY": "1"}
    r = subprocess.run(["npx", "--yes", "hyperframes@0.8.166", "transcribe", str(wav), "-l", "fr", "-m", "small", "-e", "whisper",
                        "--json", "-d", str(travail)], capture_output=True, text=True, env=env)
    if r.returncode != 0 or not (travail / "transcript.json").exists():
        sys.exit(f"Transcription impossible pour {nom} : {r.stdout[-300:]} {r.stderr[-300:]}")
    mots = json.loads((travail / "transcript.json").read_text())
    cache.write_text(json.dumps(mots, ensure_ascii=False))
    cle.write_text(signature)
    return mots


def aligner(a: np.ndarray, sr: int, textes: list[str], mots: list[dict]) -> list[tuple[float, float]]:
    """Bornes de chaque phrase dans le bloc : le texte lu est aligné caractère par caractère sur la transcription,
    puis chaque coupure est placée au centre du silence réel qui sépare la fin d'une phrase du début de la suivante."""
    from difflib import SequenceMatcher
    W, wi = [], []
    for k, m in enumerate(mots):
        n = _normaliser(m["text"])
        if n:
            W.append(n)
            wi += [k] * len(n) + [k]
    Wc = " ".join(W)
    S, spans = "", []
    for t in textes:
        n = _normaliser(t)
        spans.append((len(S), len(S) + len(n)))
        S += n + " "
    carte = {}
    for b in SequenceMatcher(None, S, Wc, autojunk=False).get_matching_blocks():
        for j in range(b.size):
            carte[b.a + j] = b.b + j
    debuts, fins = [], []
    for (d0, d1), t in zip(spans, textes):
        ok = [carte[c] for c in range(d0, d1) if c in carte]
        if len(ok) < 0.6 * (d1 - d0):
            sys.exit(f"Alignement incertain ({len(ok)}/{d1 - d0} caractères) pour : {t}")
        debuts.append(mots[wi[ok[0]]]["start"])
        fins.append(mots[wi[ok[-1]]]["end"])
    hop = int(0.01 * sr)
    rms = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(len(a) // hop)])
    bas = rms < rms.max() * 10 ** (-38 / 20)
    coupes = []
    for k in range(len(textes) - 1):
        f, d = fins[k], debuts[k + 1]
        i0, i1 = int(max(0.0, min(f, d) - 0.25) * 100), int((max(f, d) + 0.25) * 100)
        meilleur, cur = None, None
        for i in range(i0, min(i1, len(bas))):     # plus long silence dans la zone de jonction
            if bas[i] and cur is None:
                cur = i
            if (not bas[i] or i == i1 - 1) and cur is not None:
                if meilleur is None or i - cur > meilleur[1] - meilleur[0]:
                    meilleur = (cur, i)
                cur = None
        coupes.append((meilleur[0] + meilleur[1]) / 200 if meilleur else (f + d) / 2)
    bornes = [max(0.0, debuts[0] - 0.15)] + coupes + [min(len(a) / sr, fins[-1] + 0.3)]
    if any(b1 <= b0 for b0, b1 in zip(bornes, bornes[1:])):
        sys.exit("Alignement incohérent : bornes non croissantes")
    return list(zip(bornes, bornes[1:]))


def split_block(a: np.ndarray, sr: int, weights: list[int]) -> list[tuple[float, float]] | None:
    """Coupe un bloc lu d'une traite en len(weights) phrases.

    Les frontières attendues sont placées en « temps de parole » (silences retirés) au prorata des syllabes :
    les longues pauses que la voix Gemini marque à l'intérieur des phrases ne décalent plus le découpage.
    Une programmation dynamique choisit, près de chaque frontière attendue, le silence le plus long ; puis chaque
    phrase est validée sur sa durée de parole réelle (et non sur sa durée avec silences)."""
    n = len(weights)
    hop = int(0.01 * sr)
    frames = len(a) // hop
    rms = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(frames)])
    low = rms < rms.max() * 10 ** (-38 / 20)
    voiced = np.where(~low)[0]
    s0, s1 = voiced[0], voiced[-1]
    vcum = np.concatenate([[0], np.cumsum(~low)])          # trames parlées avant la trame i
    gaps, start = [], None
    for i in range(s0, s1 + 1):
        if low[i] and start is None:
            start = i
        if not low[i] and start is not None:
            if (i - start) * 0.01 >= 0.07:
                gaps.append(((start + i) / 2 * 0.01, (i - start) * 0.01, vcum[start]))
            start = None
    T0, T1 = s0 * 0.01, (s1 + 1) * 0.01
    if n == 1:
        return [(T0, T1)]
    if len(gaps) < n - 1:
        return None
    Vtot = vcum[s1 + 1] - vcum[s0]
    cum = np.cumsum(weights) / sum(weights)
    attendu = [vcum[s0] + Vtot * c for c in cum[:-1]]        # en trames parlées
    sigma = 0.3 * Vtot / n
    INF = float("inf")
    C = len(gaps)
    cost = [[INF] * C for _ in range(n - 1)]
    back = [[-1] * C for _ in range(n - 1)]

    def local(k, c):
        _, g, v = gaps[c]
        return ((v - attendu[k]) / sigma) ** 2 - 2.5 * min(g, 0.9) / 0.3

    for c in range(C):
        cost[0][c] = local(0, c)
    for k in range(1, n - 1):
        for c in range(C):
            best = min(((cost[k - 1][p], p) for p in range(c)), default=(INF, -1))
            if best[0] < INF:
                cost[k][c], back[k][c] = best[0] + local(k, c), best[1]
    c = min(range(C), key=lambda x: cost[n - 2][x])
    if cost[n - 2][c] == INF:
        return None
    chosen = [c]
    for k in range(n - 2, 0, -1):
        c = back[k][c]
        chosen.append(c)
    chosen = chosen[::-1]
    if min(gaps[c][1] for c in chosen) < 0.18:      # une frontière de phrase doit être un vrai silence, pas une virgule
        return None
    bornes_v = [vcum[s0]] + [gaps[c][2] for c in chosen] + [vcum[s1 + 1]]
    for (v0, v1), w in zip(zip(bornes_v, bornes_v[1:]), weights):   # validation sur la parole réelle
        ratio = (v1 - v0) / (Vtot * w / sum(weights))
        if not 0.55 <= ratio <= 1.6 + 6 / w:
            return None
    bounds = [T0] + [gaps[c][0] for c in chosen] + [T1]
    return list(zip(bounds, bounds[1:]))


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
        raw = gemini_audio(cfg, tok)
        ident = {"moteur": "gemini", "modele": vcfg["modele"], "voix": vcfg["voix"], "brouillon": False}
    elif moteur == "kokoro":
        k, rk = load_kokoro(), vcfg.get("repli_kokoro", vcfg)
        raw = {}
        for ph in cfg["phrases"]:
            a, sr = k.create(ph.get("tts_kokoro", ph.get("dit", ph["texte"])), voice=rk["voix"], speed=rk.get("vitesse", 1.0), lang=rk["langue"])
            raw[ph["id"]] = (np.asarray(a, dtype=np.float32), sr)
        ident = {"moteur": "kokoro", "modele": "kokoro-v1.0", "voix": rk["voix"], "brouillon": True}
    else:
        sys.exit(f"Moteur de voix inconnu : {moteur}")
    (BUILD / "voix").mkdir(parents=True, exist_ok=True)
    pieces, chrono = [], []
    t = float(vcfg.get("debut_s", 0.2))
    pieces.append(np.zeros(int(t * SR_OUT), dtype=np.float32))
    for ph in cfg["phrases"]:
        spoken = ph.get("dit", ph["texte"])
        a, sr = raw[ph["id"]]
        audio = level(tempo(trim(resample(a, sr, SR_OUT), SR_OUT, thresh_db=-40.0, keep=0.05), SR_OUT,
                            float(ph.get("tempo", 1.0))), SR_OUT)   # -40 dB : souffles d'attaque exclus, consonnes gardées
        sf.write(BUILD / f"voix/phrase_{ph['id']:02d}.wav", audio, SR_OUT, subtype="PCM_24")
        d = len(audio) / SR_OUT
        words = word_timings(tok, ph["texte"], spoken, audio, SR_OUT)
        for w in words:
            w["debut"] = round(w["debut"] + t, 3)
            w["fin"] = round(w["fin"] + t, 3)
        chrono.append({
            "id": ph["id"], "cle": ph["cle"], "seq": ph["seq"], "texte": ph["texte"],
            "phonemes": tok.phonemize(spoken, "fr-fr"),
            "debut": round(t, 3), "fin": round(t + d, 3), "duree": round(d, 3), "mots": words,
        })
        pieces.append(audio)
        fin_seq = ph is cfg["phrases"][-1] or cfg["phrases"][cfg["phrases"].index(ph) + 1]["seq"] != ph["seq"]
        pause = float(ph.get("pause", vcfg["pause_fin_sequence"] if fin_seq else vcfg["pause_defaut"]))
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
