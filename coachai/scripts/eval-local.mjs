#!/usr/bin/env node
/**
 * Run heuristic eval on saved API JSON (no deploy).
 *
 * Usage:
 *   node scripts/eval-local.mjs coaching ./sample-coaching.json
 *   node scripts/eval-local.mjs training ./sample-training.json
 *   node scripts/eval-local.mjs both ./sample-both.json   # { "coaching": {...}, "training": {...} }
 *   curl -s .../matches/1/coaching (saved) | node scripts/eval-local.mjs coaching -
 */

import fs from "fs";
import { evaluateCoachOutputs, evaluateCoachingPayload, evaluateTrainingPayload, PRESENTATION_RUBRIC } from "../src/eval.js";

function readInput(path) {
  if (path === "-") return fs.readFileSync(0, "utf8");
  return fs.readFileSync(path, "utf8");
}

const mode = process.argv[2];
const file = process.argv[3];

if (!mode || (mode !== "rubric" && !file)) {
  console.error(`Usage:
  node scripts/eval-local.mjs rubric
  node scripts/eval-local.mjs coaching <file.json|->
  node scripts/eval-local.mjs training <file.json|->
  node scripts/eval-local.mjs both <file.json|->`);
  process.exit(1);
}

if (mode === "rubric") {
  console.log(JSON.stringify(PRESENTATION_RUBRIC, null, 2));
  process.exit(0);
}

const text = readInput(file);
const data = JSON.parse(text);

let out;
if (mode === "coaching") {
  out = { coaching: evaluateCoachingPayload(data), presentationRubric: PRESENTATION_RUBRIC };
} else if (mode === "training") {
  out = { training: evaluateTrainingPayload(data), presentationRubric: PRESENTATION_RUBRIC };
} else if (mode === "both") {
  out = evaluateCoachOutputs({ coaching: data.coaching, training: data.training });
} else {
  console.error("mode must be rubric | coaching | training | both");
  process.exit(1);
}

console.log(JSON.stringify(out, null, 2));
