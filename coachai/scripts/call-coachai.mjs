#!/usr/bin/env node
/**
 * Call the CoachAI worker against a match JSON file.
 *
 * Usage:
 *   npm run coachai:call -- --file data/match.json --focal "Rafael Nadal"
 *   npm run coachai:call -- --file data/match.json --endpoint coaching --points 120
 *
 * Prereq: worker running, e.g. `npm run dev` (port 8790 by default).
 */

import { readFile } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const COACHAI_ROOT = resolve(__dirname, "..");

function parseArgs(argv) {
  const out = {
    file: resolve(COACHAI_ROOT, "data", "match.json"),
    base: process.env.COACHAI_URL || "http://127.0.0.1:8790",
    focal: null,
    endpoint: "both",
    points: null,
    help: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--help" || a === "-h") out.help = true;
    else if (a === "--file" || a === "-f") out.file = resolve(COACHAI_ROOT, argv[++i] || "");
    else if (a === "--base" || a === "-b") out.base = argv[++i] || out.base;
    else if (a === "--focal") out.focal = argv[++i] || null;
    else if (a === "--endpoint" || a === "-e") out.endpoint = argv[++i] || "both";
    else if (a === "--points" || a === "-p") out.points = parseInt(argv[++i], 10);
  }
  return out;
}

function printHelp() {
  console.log(`
CoachAI test client

  Place a match JSON file at coachai/data/match.json (or pass --file).

  Start the worker first:
    cd coachai && npm run dev

  Examples:
    npm run coachai:call
    npm run coachai:call -- --file data/match.json --focal "Roger Federer"
    npm run coachai:call -- --endpoint coaching --points 80
    COACHAI_URL=https://coachai-dev.example.workers.dev npm run coachai:call

  Options:
    --file, -f     Path to match JSON (default: data/match.json)
    --base, -b     Worker origin (default: http://127.0.0.1:8790 or COACHAI_URL)
    --focal        Player name (must match a key in match.players); default: first player
    --endpoint, -e coaching | training | both (default: both)
    --points, -p   For coaching only: truncate history to this many points (mid-match sim)
`);
}

function pickFocal(matchData, focal) {
  const names = Object.keys(matchData.players || {});
  if (!names.length) throw new Error("match JSON has no players object / keys");
  if (focal) {
    if (!names.includes(focal)) {
      throw new Error(`focal "${focal}" not in players: ${names.join(", ")}`);
    }
    return focal;
  }
  return names[0];
}

function sliceForMidMatch(matchData, n) {
  if (n == null || !Number.isFinite(n) || n < 1) return matchData;
  const copy = structuredClone(matchData);
  const h = copy.history;
  if (Array.isArray(h) && h.length > n) copy.history = h.slice(0, n);
  return copy;
}

async function post(base, path, body) {
  const url = `${base.replace(/\/+$/, "")}${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    json = { _raw: text };
  }
  return { ok: res.ok, status: res.status, json };
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    printHelp();
    process.exit(0);
  }

  const raw = await readFile(args.file, "utf8");
  let matchData;
  try {
    matchData = JSON.parse(raw);
  } catch (e) {
    console.error("Invalid JSON in", args.file, e.message);
    process.exit(1);
  }

  const focalPlayer = pickFocal(matchData, args.focal);
  const ep = String(args.endpoint).toLowerCase();

  console.log("File:", args.file);
  console.log("Base:", args.base);
  console.log("Focal:", focalPlayer);

  if (ep === "both" || ep === "coaching") {
    const payload = sliceForMidMatch(matchData, args.points);
    if (args.points) console.log("Coaching: history truncated to", payload.history?.length ?? 0, "points");
    console.log("\n--- POST /coaching ---\n");
    const r = await post(args.base, "/coaching", { matchData: payload, focalPlayer });
    console.log("Status:", r.status, r.ok ? "OK" : "FAIL");
    console.log(JSON.stringify(r.json, null, 2));
  }

  if (ep === "both" || ep === "training") {
    console.log("\n--- POST /training ---\n");
    const r = await post(args.base, "/training", { matchData, focalPlayer });
    console.log("Status:", r.status, r.ok ? "OK" : "FAIL");
    console.log(JSON.stringify(r.json, null, 2));
  }

  if (!["both", "coaching", "training"].includes(ep)) {
    console.error('Unknown --endpoint; use coaching | training | both');
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
