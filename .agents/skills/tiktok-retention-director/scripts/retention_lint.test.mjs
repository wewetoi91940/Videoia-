import assert from "node:assert/strict";
import test from "node:test";
import { lint, screenBlocks } from "./retention_lint.mjs";

const frame = (n, title, keys, narrative = "") =>
  `## Frame ${n} — ${title}\n\n${Object.entries(keys).map(([k, v]) => `- ${k}: ${v}`).join("\n")}\n\n${narrative}\n`;
const shot = { image: "archive.jpg · PD", camera: "ken-burns in", animation: "fade", on_screen: 'label "Paris"', sfx: "none", transition_in: "cut" };
const head = "---\nformat: 1080x1920\nduration: 12s\n---\n\n";

const good = head
  + frame(1, "Hook", { ...shot, duration: "2s", beat_role: "hook", hook_type: "curiosity", voiceover: '"Pourquoi Paris était sous l\'eau ?"',
    new_info: "Paris inondé", open_loop: "Q1 — pourquoi", on_screen: 'title "Paris sous l\'eau"', changes: "0, 1" })
  + frame(2, "Context", { ...shot, duration: "3s", beat_role: "context", voiceover: '"Janvier 1910, la Seine sort de son lit."',
    new_info: "date et lieu", changes: "0, 1.5" })
  + frame(3, "Turn", { ...shot, duration: "3s", beat_role: "turn", voiceover: '"Mais la pluie ne suffit pas à tout expliquer."',
    new_info: "pluie insuffisante", changes: "0, 1.5" })
  + frame(4, "Reveal", { ...shot, duration: "4s", beat_role: "reveal", voiceover: '"Les sols gelés ont tout renvoyé vers le fleuve."',
    new_info: "sols gelés", closes: "Q1", changes: "0, 2" });

test("a complete plan passes without error", () => {
  const r = lint(good);
  assert.deepEqual(r.errors, []);
  assert.equal(r.stats.frames, 4);
  assert.equal(r.stats.total, 12);
});

test("landscape format, missing new_info, unclosed loop and a long still are errors", () => {
  const bad = good.replace("format: 1080x1920", "format: 1920x1080")
    .replace("- new_info: pluie insuffisante\n", "")
    .replace("- closes: Q1\n", "")
    .replace("- changes: 0, 2\n", "- changes: 0\n")
    .replace("- duration: 4s", "- duration: 7s");
  const r = lint(bad);
  const all = r.errors.join("\n");
  assert.match(all, /format/);
  assert.match(all, /Frame 3: no `new_info`/);
  assert.match(all, /open loop Q1 is never closed/);
  assert.match(all, /without a visible change/);
});

test("a hook that is not first, too long or full of filler is flagged", () => {
  const r = lint(good.replace("beat_role: hook", "beat_role: context")
    .replace("Pourquoi Paris était sous l'eau ?", "Bonjour à tous, dans cette vidéo je vais vous parler longuement de Paris et de la Seine en hiver"));
  assert.match(r.errors.join("\n"), /first frame must have `beat_role: hook`/);
  const w = r.warnings.join("\n");
  assert.match(w, /hook line has \d+ words/);
  assert.match(w, /filler phrase "dans cette vidéo"/);
});

test("no payoff is an error; an early payoff is a warning", () => {
  const noPay = lint(good.replace("beat_role: reveal", "beat_role: development"));
  assert.match(noPay.errors.join("\n"), /no `reveal` or `conclusion`/);
  const early = lint(good.replace("beat_role: turn", "beat_role: reveal").replace("beat_role: reveal\n- voiceover: \"Les sols", "beat_role: development\n- voiceover: \"Les sols"));
  assert.match(early.warnings.join("\n"), /payoff lands before the last quarter/);
});

test("on-screen blocks keep their role; the hook counts only its title", () => {
  assert.deepEqual(screenBlocks('title "La Seine arrête les horloges" · label "PARIS · JANVIER 1910"'),
    [{ role: "title", text: "La Seine arrête les horloges" }, { role: "label", text: "PARIS · JANVIER 1910" }]);
  const r = lint(good.replace(`on_screen: title "Paris sous l'eau"`, `on_screen: title "Paris sous l'eau" · label "JANVIER 1910 · PARIS · SEINE · CRUE"`));
  assert.doesNotMatch(r.warnings.join("\n"), /on-screen hook text/);
});
