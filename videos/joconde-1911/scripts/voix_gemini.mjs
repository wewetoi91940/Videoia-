#!/usr/bin/env node
// Synthèse Gemini phrase par phrase, via le module officiel du skill HyperFrames media-use
// (.agents/skills/media-use/audio/scripts/lib/gemini-tts.mjs).
// Clé lue dans l'environnement : GEMINI_API_KEY ou GOOGLE_API_KEY (jamais écrite dans un fichier ni affichée).
//
// Usage : node scripts/voix_gemini.mjs build/voix_gemini/travaux.json
// travaux.json : { "modele", "voix", "jobs": [{ "id", "texte", "style", "wav" }] }
// Cache : un fichier <wav>.json mémorise (texte, style, voix, modèle) ; une phrase inchangée n'est pas régénérée,
// ce qui économise le quota gratuit.
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const lib = resolve(here, "../../../.agents/skills/media-use/audio/scripts/lib/gemini-tts.mjs");
const { synthesizeGemini, GEMINI_TTS_MODELS } = await import(lib);

const cfg = JSON.parse(readFileSync(process.argv[2], "utf8"));
if (!process.env.GEMINI_API_KEY && !process.env.GOOGLE_API_KEY) {
  console.error("Clé absente : définir GEMINI_API_KEY (ou GOOGLE_API_KEY) dans l'environnement.");
  process.exit(2);
}
if (!GEMINI_TTS_MODELS.includes(cfg.modele)) {
  console.error(`Modèle inconnu : ${cfg.modele}. Modèles acceptés : ${GEMINI_TTS_MODELS.join(", ")}`);
  process.exit(2);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
for (const job of cfg.jobs) {
  const key = { texte: job.texte, style: job.style, voix: cfg.voix, modele: cfg.modele };
  const side = `${job.wav}.json`;
  if (existsSync(job.wav) && existsSync(side) && readFileSync(side, "utf8") === JSON.stringify(key)) {
    results.push({ id: job.id, ok: true, cache: true });
    continue;
  }
  let res;
  for (let essai = 1; essai <= 6; essai++) {
    res = await synthesizeGemini({
      text: job.texte, voiceId: cfg.voix, model: cfg.modele, style: job.style, wavAbs: resolve(job.wav),
    });
    if (res.ok) break;
    // 429 / 503 : quota par minute ou surcharge → attente croissante ; autre erreur → abandon immédiat.
    if (!/HTTP (429|500|503)/.test(res.error ?? "")) break;
    const attente = 15000 * essai;
    console.error(`phrase ${job.id} : ${res.error.slice(0, 120)} → nouvel essai dans ${attente / 1000} s`);
    await sleep(attente);
  }
  if (res.ok) writeFileSync(side, JSON.stringify(key));
  results.push({ id: job.id, ok: res.ok, error: res.ok ? undefined : res.error });
  console.error(`phrase ${job.id} : ${res.ok ? "ok" : "ÉCHEC"}`);
}
writeFileSync(resolve(dirname(process.argv[2]), "resultats.json"), JSON.stringify(results, null, 1));
const echecs = results.filter((r) => !r.ok);
if (echecs.length) {
  console.error(`${echecs.length} phrase(s) en échec : ${echecs.map((r) => r.id).join(", ")}`);
  process.exit(1);
}
