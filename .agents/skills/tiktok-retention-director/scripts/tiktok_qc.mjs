#!/usr/bin/env node
// tiktok_qc.mjs — QC of a rendered TikTok short (tiktok-retention-director, Step 8).
//
// Measures with ffprobe / ffmpeg (no other dependency): format (1080×1920, fps, codecs), duration
// against the target, integrated loudness and true peak, silences (dead air), frozen picture, black
// frames; and writes a contact sheet — frames at 0 s, 0.5 s, 1.5 s, then evenly spaced — with TikTok's
// interface zones drawn in red, so any text or face under the interface shows at a glance.
//
//   node tiktok_qc.mjs --video renders/video.mp4 [--target 45] [--sheet renders/qc-sheet.jpg] [--json]
//   node tiktok_qc.mjs --print-checks   # the `npx hyperframes check --caption-zone` passes for the same zones
//
// Exit code 1 when an error is found.

import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { isMainModule } from "../../faceless-explainer/scripts/lib/main-module.mjs";

// TikTok interface zones on a 1080×1920 frame, as fractions (see references/vertical-direction.md).
export const ZONES = [
  { name: "top bar", x0: 0, y0: 0, x1: 1, y1: 0.083 },
  { name: "right rail", x0: 0.87, y0: 0.365, x1: 1, y1: 0.781 },
  { name: "bottom area", x0: 0, y0: 0.771, x1: 1, y1: 1 },
];
export const TARGETS = {
  width: 1080, height: 1920, fps: [24, 60], lufs: [-16, -12], truePeak: -1.0,
  silenceDb: -45, silenceEarly: 1.2, silenceLate: 2.0, earlyWindow: 10, freeze: 5.0, black: 0.25,
  durationTolerance: 0.15,
};

export function checkCommands(severity = "error") {
  return ZONES.map((z) => `npx hyperframes check --caption-zone "x0=${z.x0};y0=${z.y0};x1=${z.x1};y1=${z.y1};severity=${severity};seek=.25,.5,.75"   # ${z.name}`);
}

export function parseLoudness(stderr) {
  const tail = stderr.slice(stderr.lastIndexOf("Summary:"));
  const I = tail.match(/I:\s+(-?[\d.]+|-inf)\s+LUFS/);
  const P = tail.match(/True peak:[\s\S]*?Peak:\s+(-?[\d.]+|-inf)\s+dBFS/);
  const f = (m) => (m ? (m[1] === "-inf" ? -Infinity : Number(m[1])) : undefined);
  return { lufs: f(I), truePeak: f(P) };
}

export function parseIntervals(stderr, key) {
  // silencedetect: "silence_start: 3.2" / "silence_end: 5.1 | silence_duration: 1.9"
  // freezedetect / blackdetect write lavfi.<key>_start / _end metadata or "black_start:0 black_end:0.5"
  const out = [];
  const re = new RegExp(`${key}_(start|end)[:=]\\s*(-?[\\d.]+)`, "g");
  let cur = null;
  for (const m of stderr.matchAll(re)) {
    const v = Number(m[2]);
    if (m[1] === "start") cur = { start: v };
    else if (cur) {
      out.push({ start: cur.start, end: v, duration: Math.round((v - cur.start) * 100) / 100 });
      cur = null;
    }
  }
  if (cur) out.push({ start: cur.start, end: null, duration: null });
  return out;
}

function probe(video) {
  const raw = execFileSync("ffprobe", ["-v", "error", "-show_entries",
    "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels:format=duration,size",
    "-of", "json", video], { encoding: "utf8" });
  return JSON.parse(raw);
}

function analyse(video) {
  const T = TARGETS;
  const r = spawnSync("ffmpeg", ["-hide_banner", "-nostats", "-i", video,
    "-af", `ebur128=peak=true,silencedetect=noise=${T.silenceDb}dB:d=${T.silenceEarly}`,
    "-vf", `freezedetect=n=0.003:d=${T.freeze},blackdetect=d=${T.black}:pix_th=0.10,metadata=mode=print`,
    "-f", "null", "-"], { encoding: "utf8", maxBuffer: 1 << 28 });
  const err = r.stderr || "";
  return { ...parseLoudness(err), silences: parseIntervals(err, "silence"), freezes: parseIntervals(err, "freeze"),
    blacks: parseIntervals(err, "black") };
}

export function sheetTimes(duration, n = 12) {
  const fixed = [0, 0.5, 1.5];
  const rest = n - fixed.length;
  const times = [...fixed];
  for (let i = 1; i <= rest; i++) times.push(Math.round((1.5 + ((duration - 1.6) * i) / rest) * 100) / 100);
  return times.filter((t) => t < duration);
}

function sheet(video, duration, out) {
  const dir = mkdtempSync(join(tmpdir(), "tiktok-qc-"));
  try {
    const boxes = ZONES.map((z) => `drawbox=x=iw*${z.x0}:y=ih*${z.y0}:w=iw*${(z.x1 - z.x0).toFixed(3)}:h=ih*${(z.y1 - z.y0).toFixed(3)}:color=red@0.38:t=fill`).join(",");
    const times = sheetTimes(duration);
    times.forEach((t, i) => {
      execFileSync("ffmpeg", ["-v", "error", "-y", "-ss", String(t), "-i", video, "-frames:v", "1",
        // yuv444p first: in yuv420p, ffmpeg's drawbox paints the boxes opaque and hides what they should reveal
        "-vf", `format=yuv444p,${boxes},scale=270:480`, join(dir, `${String(i).padStart(2, "0")}.png`)]);
    });
    const cols = Math.min(6, times.length);
    execFileSync("ffmpeg", ["-v", "error", "-y", "-framerate", "1", "-i", join(dir, "%02d.png"),
      "-vf", `tile=${cols}x${Math.ceil(times.length / cols)}:padding=6:color=0x202020`, "-frames:v", "1", "-q:v", "3", out]);
    return times;
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

export function evaluate(info, target) {
  const T = TARGETS;
  const errors = [];
  const warnings = [];
  const v = info.streams.find((s) => s.codec_type === "video");
  const a = info.streams.find((s) => s.codec_type === "audio");
  const duration = Number(info.format.duration);
  if (!v) errors.push("no video stream");
  else {
    if (v.width !== T.width || v.height !== T.height) errors.push(`frame is ${v.width}×${v.height}, expected ${T.width}×${T.height}`);
    const [n, d] = String(v.r_frame_rate).split("/").map(Number);
    const fps = d ? n / d : n;
    if (!(fps >= T.fps[0] && fps <= T.fps[1])) errors.push(`frame rate ${fps} fps outside ${T.fps[0]}–${T.fps[1]}`);
    if (v.codec_name !== "h264") warnings.push(`video codec ${v.codec_name} (H.264 is the safest upload)`);
    if (v.pix_fmt && v.pix_fmt !== "yuv420p") warnings.push(`pixel format ${v.pix_fmt} (yuv420p expected)`);
  }
  if (!a) errors.push("no audio stream");
  else if (a.codec_name !== "aac") warnings.push(`audio codec ${a.codec_name} (AAC expected)`);
  if (target && Math.abs(duration - target) / target > T.durationTolerance) warnings.push(`duration ${duration.toFixed(1)} s vs target ${target} s`);
  if (Number(info.format.size) > 287e6) warnings.push(`file is ${(info.format.size / 1e6).toFixed(0)} MB: some upload paths refuse large files`);
  const m = info.measures || {};
  if (a && m.lufs !== undefined) {
    if (!(m.lufs >= T.lufs[0] && m.lufs <= T.lufs[1])) errors.push(`integrated loudness ${m.lufs} LUFS outside ${T.lufs[0]}…${T.lufs[1]}`);
    if (m.truePeak > T.truePeak) errors.push(`true peak ${m.truePeak} dBFS above ${T.truePeak} dBTP`);
  }
  for (const s of m.silences || []) {
    const len = s.duration ?? duration - s.start;
    const tail = s.start >= duration - 4; // end card
    if (s.start < T.earlyWindow) errors.push(`silence of ${len.toFixed(1)} s at ${s.start.toFixed(1)} s (first ${T.earlyWindow} s)`);
    else if (len > T.silenceLate && !tail) warnings.push(`silence of ${len.toFixed(1)} s at ${s.start.toFixed(1)} s — intended?`);
  }
  for (const f of m.freezes || []) {
    const len = f.duration ?? duration - f.start;
    (f.start < T.earlyWindow ? errors : warnings).push(`picture frozen ${len.toFixed(1)} s from ${f.start.toFixed(1)} s`);
  }
  for (const b of m.blacks || []) {
    if (b.start < 0.05) errors.push(`black at the start (${b.start}–${b.end} s): the paused thumbnail is empty`);
    else warnings.push(`black frames ${b.start}–${b.end} s`);
  }
  return { errors, warnings, duration };
}

function main(argv) {
  const flag = (name, def) => {
    const i = argv.indexOf(`--${name}`);
    return i >= 0 && i + 1 < argv.length ? argv[i + 1] : def;
  };
  if (argv.includes("--print-checks")) {
    console.log(checkCommands().join("\n"));
    return 0;
  }
  const video = flag("video");
  if (!video) {
    console.error("usage: tiktok_qc.mjs --video <file.mp4> [--target <s>] [--sheet <out.jpg>] [--json] | --print-checks");
    return 2;
  }
  statSync(video);
  const target = flag("target") ? Number(flag("target")) : undefined;
  const info = probe(video);
  info.measures = analyse(video);
  const res = evaluate(info, target);
  const out = flag("sheet");
  if (out) res.sheet = { path: out, times: sheet(video, res.duration, out) };
  res.measures = info.measures;
  if (argv.includes("--json")) console.log(JSON.stringify(res, null, 1));
  else {
    const m = info.measures;
    const v = info.streams.find((s) => s.codec_type === "video") || {};
    console.log(`tiktok_qc: ${v.width}×${v.height} · ${res.duration.toFixed(2)} s · ${m.lufs} LUFS · true peak ${m.truePeak} dBFS · `
      + `${m.silences.length} silence(s) · ${m.freezes.length} freeze(s) · ${m.blacks.length} black segment(s)`);
    for (const e of res.errors) console.log(`  ✗ ${e}`);
    for (const w of res.warnings) console.log(`  ⚠ ${w}`);
    if (res.sheet) console.log(`  sheet: ${res.sheet.path} (frames at ${res.sheet.times.join(", ")} s; TikTok interface in red)`);
    console.log(res.errors.length ? `✗ ${res.errors.length} error(s)` : `✓ no error, ${res.warnings.length} warning(s)`);
  }
  return res.errors.length ? 1 : 0;
}

if (isMainModule(import.meta.url)) process.exit(main(process.argv.slice(2)));
