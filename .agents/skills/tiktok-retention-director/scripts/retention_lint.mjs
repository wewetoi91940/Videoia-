#!/usr/bin/env node
// retention_lint.mjs — check a TikTok STORYBOARD.md against the retention rules of
// tiktok-retention-director (Steps 3–5) before anything is built.
//
// Reads the standard storyboard with the parser vendored by /faceless-explainer, plus the
// direction keys this skill adds per frame (all optional for the core parser, kept under `extra`):
//   beat_role   hook | context | development | turn | reveal | conclusion
//   hook_type   curiosity | contradiction | surprising_fact | suspense | unexpected_consequence
//   new_info    what this beat adds              open_loop  Q1 — <question>   closes  Q1[, Q2]
//   image · camera · animation · on_screen · sfx   (the shot table)
//   changes     seconds from the frame start where the picture visibly changes: "0, 1.8, 3.4"
//
//   node retention_lint.mjs --storyboard STORYBOARD.md [--lang fr|en] [--target 45] [--json]
//
// Exit code 1 when an error is found; warnings never fail the run.

import { readFileSync } from "node:fs";
import { parseStoryboard } from "../../faceless-explainer/scripts/lib/storyboard.mjs";
import { isMainModule } from "../../faceless-explainer/scripts/lib/main-module.mjs";

export const HOOK_TYPES = ["curiosity", "contradiction", "surprising_fact", "suspense", "unexpected_consequence"];
export const BEAT_ROLES = ["hook", "context", "development", "turn", "reveal", "conclusion"];
export const SHOT_KEYS = ["image", "camera", "animation", "on_screen", "sfx"];
export const LIMITS = {
  hookFrameMax: 3.0, // s — the hook line itself should end by ~2 s
  hookWords: { fr: 12, en: 10 },
  hookScreenWords: 6,
  contextEnd: 7.0, // s — minimal context done by then
  wordsPerSecond: { fr: 3.2, en: 3.0 },
  gapWarn: 4.0, // s between two visible changes
  gapError: 5.5,
  gapEarly: 3.0, // in the first `earlyWindow` seconds
  earlyWindow: 10.0,
  screenWords: 9,
  targetTolerance: 0.15,
  payoffShare: 0.25, // a reveal/conclusion starts in the last quarter
  maxOpenLoops: 2,
  repeatOverlap: 0.6,
};
const FILLERS = {
  fr: ["dans cette vidéo", "aujourd'hui on va", "aujourd’hui on va", "bonjour", "salut à tous", "salut tout le monde",
    "abonne-toi", "abonnez-vous", "n'oubliez pas", "n’oubliez pas", "je vais vous expliquer", "laissez-moi vous",
    "comme vous le savez", "vous allez être choqué", "incroyable mais vrai"],
  en: ["in this video", "today we", "hey guys", "hi everyone", "let's dive", "let me explain", "don't forget to",
    "smash that", "subscribe", "as you know", "you won't believe"],
};

const words = (s) => (s || "").split(/\s+/).filter((w) => /[\p{L}\p{N}]/u.test(w));
const contentWords = (s) => new Set(words(s.toLowerCase()).map((w) => w.replace(/[^\p{L}\p{N}]/gu, "")).filter((w) => w.length >= 4));
const num = (s) => {
  const m = String(s ?? "").match(/(\d+(?:[.,]\d+)?)/);
  return m ? Number(m[1].replace(",", ".")) : undefined;
};
const r1 = (x) => Math.round(x * 10) / 10;

// on_screen: `title "…" · label "…"` → [{ role, text }]; an unquoted value is one block without a role.
export function screenBlocks(s) {
  const raw = String(s || "");
  const q = [...raw.matchAll(/(?:\b(title|label|number|quote|source)\s+)?["“]([^"”]+)["”]/gi)]
    .map((m) => ({ role: (m[1] || "").toLowerCase(), text: m[2] }));
  return q.length ? q : raw ? [{ role: "", text: raw.replace(/^(title|label|number|quote|source)\s+/i, "") }] : [];
}

export function lint(source, { lang = "fr", target } = {}) {
  const L = LIMITS;
  const errors = [];
  const warnings = [];
  const err = (frame, msg) => errors.push(frame ? `Frame ${frame}: ${msg}` : msg);
  const warn = (frame, msg) => warnings.push(frame ? `Frame ${frame}: ${msg}` : msg);
  const lg = lang === "en" ? "en" : "fr";

  const sb = parseStoryboard(source);
  const frames = sb.frames;
  if (!frames.length) {
    err(null, "no frame found (expected `## Frame N — Title` sections)");
    return { errors, warnings, stats: {} };
  }
  const fmt = String(sb.globals.format || "").toLowerCase().replace(/\s/g, "");
  if (!["1080x1920", "1080×1920", "portrait"].includes(fmt)) err(null, `format is "${sb.globals.format ?? "missing"}", expected 1080x1920`);
  const tgt = target ?? num(sb.globals.extra?.duration);

  // timing
  let t = 0;
  const rows = frames.map((f) => {
    const x = f.extra || {};
    const d = f.durationSeconds;
    const id = f.number ?? f.index;
    if (!(d > 0)) err(id, "missing or zero `duration`");
    const row = { id, start: t, dur: d > 0 ? d : 0, x, vo: f.voiceover || "", transition: f.transitionIn };
    t += row.dur;
    return row;
  });
  const total = t;

  // hook
  const h = rows[0];
  if (h.x.beat_role !== "hook") err(h.id, "the first frame must have `beat_role: hook`");
  if (!h.x.hook_type) warn(h.id, "no `hook_type` (one of " + HOOK_TYPES.join(", ") + ")");
  else if (!HOOK_TYPES.includes(h.x.hook_type)) err(h.id, `unknown hook_type "${h.x.hook_type}"`);
  if (h.dur > L.hookFrameMax) warn(h.id, `hook frame lasts ${r1(h.dur)} s; the hook line must still land by ~2 s`);
  const hw = words(h.vo).length;
  if (hw > L.hookWords[lg]) warn(h.id, `hook line has ${hw} words (≤ ${L.hookWords[lg]})`);
  if (!h.vo) warn(h.id, "the hook frame has no voiceover");
  const hb = screenBlocks(h.x.on_screen);
  const titles = hb.filter((b) => b.role === "title");
  const hs = (titles.length ? titles : hb).reduce((a, b) => a + words(b.text).length, 0); // the hook text = its title
  if (!h.x.on_screen) warn(h.id, "no on-screen hook text (many viewers start without sound)");
  else if (hs > L.hookScreenWords) warn(h.id, `on-screen hook text has ${hs} words (≤ ${L.hookScreenWords})`);

  // per frame
  const ctx = rows.find((r) => r.x.beat_role === "context");
  if (!ctx) warn(null, "no `beat_role: context` frame: make sure who / where / when is clear by ~6 s");
  else if (ctx.start + ctx.dur > L.contextEnd) warn(ctx.id, `context ends at ${r1(ctx.start + ctx.dur)} s (aim ≤ ${L.contextEnd} s)`);
  let prevWords = null;
  for (const r of rows) {
    if (r.x.beat_role && !BEAT_ROLES.includes(r.x.beat_role)) err(r.id, `unknown beat_role "${r.x.beat_role}"`);
    if (!r.x.beat_role) warn(r.id, "no `beat_role`");
    if (!r.x.new_info) (r.vo ? err : warn)(r.id, "no `new_info`: every beat must add something");
    const missing = SHOT_KEYS.filter((k) => !r.x[k]);
    if (missing.length) warn(r.id, `shot table incomplete: ${missing.join(", ")}`);
    if (!r.transition) warn(r.id, "no `transition_in`");
    const n = words(r.vo).length;
    if (r.dur > 0 && n / r.dur > L.wordsPerSecond[lg]) warn(r.id, `${n} words in ${r1(r.dur)} s = ${r1(n / r.dur)} words/s (≤ ${L.wordsPerSecond[lg]})`);
    for (const b of screenBlocks(r.x.on_screen)) {
      if (words(b.text).length > L.screenWords) warn(r.id, `on-screen text "${b.text}" is longer than ${L.screenWords} words`);
    }
    const low = r.vo.toLowerCase();
    for (const f of FILLERS[lg]) if (low.includes(f)) warn(r.id, `filler phrase "${f}" — cut it or say the thing itself`);
    const cw = contentWords(r.vo);
    if (prevWords && cw.size >= 3) {
      const inter = [...cw].filter((w) => prevWords.has(w)).length;
      if (inter / Math.min(cw.size, prevWords.size) > L.repeatOverlap) warn(r.id, "repeats most of the previous line");
    }
    prevWords = cw.size ? cw : prevWords;
  }

  // visual changes
  const changes = [];
  for (const r of rows) {
    const raw = r.x.changes;
    if (!raw) warn(r.id, "no `changes:` — counted as one change at the frame start");
    const list = raw ? String(raw).split(/[,;\s]+/).map(Number).filter((x) => Number.isFinite(x)) : [0];
    for (const c of list) {
      if (c < 0 || c > r.dur + 1e-6) err(r.id, `change at ${c} s is outside the frame (0–${r1(r.dur)} s)`);
      else changes.push(r.start + c);
    }
    if (!list.includes(0)) changes.push(r.start); // every cut is a change
  }
  changes.sort((a, b) => a - b);
  changes.push(total);
  let maxGap = 0;
  for (let i = 1; i < changes.length; i++) {
    const a = changes[i - 1];
    const gap = changes[i] - a;
    maxGap = Math.max(maxGap, gap);
    const at = rows.find((r) => a >= r.start - 1e-6 && a < r.start + r.dur - 1e-6)?.id;
    if (gap > L.gapError) err(at, `${r1(gap)} s without a visible change from ${r1(a)} s`);
    else if (gap > L.gapWarn) warn(at, `${r1(gap)} s without a visible change from ${r1(a)} s`);
    else if (a < L.earlyWindow && gap > L.gapEarly) warn(at, `${r1(gap)} s without change inside the first ${L.earlyWindow} s`);
  }

  // open loops
  const open = new Map();
  const closedIds = new Set();
  let maxOpen = 0;
  for (const r of rows) {
    for (const id of String(r.x.closes || "").split(/[,\s]+/).filter(Boolean)) {
      if (!open.has(id)) (closedIds.has(id) ? warn : err)(r.id, `closes ${id}, which is not open at this point`);
      open.delete(id);
      closedIds.add(id);
    }
    if (r.x.open_loop) {
      const id = String(r.x.open_loop).trim().split(/[\s—–-]+/)[0];
      open.set(id, r.id);
    }
    maxOpen = Math.max(maxOpen, open.size);
  }
  for (const [id, fr] of open) err(fr, `open loop ${id} is never closed (add \`closes: ${id}\` where it is answered)`);
  if (!rows.slice(0, 2).some((r) => r.x.open_loop)) warn(null, "no open loop in the first two frames: what question keeps the viewer?");
  if (maxOpen > L.maxOpenLoops) warn(null, `${maxOpen} questions open at once (≤ ${L.maxOpenLoops})`);

  // arc
  const pay = rows.filter((r) => ["reveal", "conclusion"].includes(r.x.beat_role));
  if (!pay.length) err(null, "no `reveal` or `conclusion` frame: the hook is never paid off");
  else if (!pay.some((r) => r.start >= (1 - L.payoffShare) * total - 1e-6)) warn(pay.at(-1).id, "the payoff lands before the last quarter: retention may drop before the end");
  if (total >= 30 && !rows.some((r) => r.x.beat_role === "turn")) warn(null, "no `turn` (re-hook) in a video of 30 s or more");
  if (tgt && Math.abs(total - tgt) / tgt > L.targetTolerance) warn(null, `total ${r1(total)} s vs target ${tgt} s (±${L.targetTolerance * 100} %)`);

  const nWords = rows.reduce((a, r) => a + words(r.vo).length, 0);
  const stats = { frames: rows.length, total: r1(total), target: tgt ?? null, words: nWords,
    wordsPerSecond: total ? r1(nWords / total) : 0, maxGapWithoutChange: r1(maxGap), loops: closedIds.size + open.size };
  return { errors, warnings, stats, parserWarnings: sb.warnings.map((w) => w.message) };
}

function main(argv) {
  const flag = (name, def) => {
    const i = argv.indexOf(`--${name}`);
    return i >= 0 && i + 1 < argv.length ? argv[i + 1] : def;
  };
  const path = flag("storyboard", "STORYBOARD.md");
  const res = lint(readFileSync(path, "utf8"), { lang: flag("lang", "fr"), target: num(flag("target")) });
  if (argv.includes("--json")) {
    console.log(JSON.stringify(res, null, 1));
  } else {
    const s = res.stats;
    console.log(`retention_lint: ${s.frames} frames · ${s.total} s${s.target ? ` (target ${s.target} s)` : ""} · ${s.words} words · ${s.wordsPerSecond} words/s · longest still ${s.maxGapWithoutChange} s`);
    for (const e of res.errors) console.log(`  ✗ ${e}`);
    for (const w of res.warnings) console.log(`  ⚠ ${w}`);
    for (const w of res.parserWarnings || []) console.log(`  ⚠ parser: ${w}`);
    console.log(res.errors.length ? `✗ ${res.errors.length} error(s), ${res.warnings.length} warning(s)` : `✓ no error, ${res.warnings.length} warning(s)`);
  }
  return res.errors.length ? 1 : 0;
}

if (isMainModule(import.meta.url)) process.exit(main(process.argv.slice(2)));
