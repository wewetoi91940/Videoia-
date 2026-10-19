import assert from "node:assert/strict";
import test from "node:test";
import { ZONES, checkCommands, evaluate, parseIntervals, parseLoudness, sheetTimes } from "./tiktok_qc.mjs";

test("zones stay inside the frame and become caption-zone passes", () => {
  for (const z of ZONES) {
    assert.ok(z.x0 >= 0 && z.x1 <= 1 && z.y0 >= 0 && z.y1 <= 1 && z.x0 < z.x1 && z.y0 < z.y1, z.name);
  }
  const cmds = checkCommands();
  assert.equal(cmds.length, ZONES.length);
  assert.match(cmds[2], /--caption-zone "x0=0;y0=0\.771;x1=1;y1=1;severity=error/);
});

test("ebur128 summary, silences and detect intervals are parsed", () => {
  const err = `[Parsed_ebur128_0 @ 0x1] Summary:\n\n  Integrated loudness:\n    I:         -14.2 LUFS\n    Threshold: -24.3 LUFS\n\n  True peak:\n    Peak:       -1.3 dBFS\n`
    + "[silencedetect @ 0x2] silence_start: 3.2\n[silencedetect @ 0x2] silence_end: 5.1 | silence_duration: 1.9\n"
    + "[blackdetect @ 0x3] black_start:0 black_end:0.4 black_duration:0.4\n"
    + "[freezedetect @ 0x4] lavfi.freezedetect.freeze_start: 12.5\nlavfi.freezedetect.freeze_start=12.5\n[freezedetect @ 0x4] lavfi.freezedetect.freeze_end: 18\n";
  assert.deepEqual(parseLoudness(err), { lufs: -14.2, truePeak: -1.3 });
  assert.deepEqual(parseIntervals(err, "silence"), [{ start: 3.2, end: 5.1, duration: 1.9 }]);
  assert.deepEqual(parseIntervals(err, "black"), [{ start: 0, end: 0.4, duration: 0.4 }]);
  assert.deepEqual(parseIntervals(err, "freeze"), [{ start: 12.5, end: 18, duration: 5.5 }]);
});

test("evaluation flags landscape, loud masters, early silence and a black first frame", () => {
  const info = {
    streams: [{ codec_type: "video", codec_name: "h264", width: 1920, height: 1080, r_frame_rate: "30/1", pix_fmt: "yuv420p" },
      { codec_type: "audio", codec_name: "aac" }],
    format: { duration: "45.0", size: "40000000" },
    measures: { lufs: -9, truePeak: -0.2, silences: [{ start: 2, end: 4, duration: 2 }], freezes: [], blacks: [{ start: 0, end: 0.4, duration: 0.4 }] },
  };
  const r = evaluate(info, 45);
  const all = r.errors.join("\n");
  assert.match(all, /1920×1080/);
  assert.match(all, /integrated loudness/);
  assert.match(all, /true peak/);
  assert.match(all, /silence of 2\.0 s at 2\.0 s/);
  assert.match(all, /black at the start/);
});

test("sheet times start with the hook moments and stay inside the video", () => {
  const t = sheetTimes(45);
  assert.deepEqual(t.slice(0, 3), [0, 0.5, 1.5]);
  assert.equal(t.length, 12);
  assert.ok(t.every((x) => x < 45));
});
