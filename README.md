# CS 5620 Final Project — Code and run instructions

**Course:** CS 5620 — AI Applications in Education  
**Instructor:** Seth Poulsen  
**Student:** Jacob Beal  
**Date:** April 2026  
**Project title:** MyBreakPoint Match Coach — intelligent tutoring for tennis strategy using structured knowledge components and an LLM (Cloudflare Workers AI) for coaching feedback.

---

## What is being submitted

For privacy and confidentiality, **only these items** are uploaded with this assignment:

- **`coachai/`** — current Match Coach (Wrangler / Workers AI tooling)
- **`old/`** — earlier Python pipeline (models, coach NLG, tests)
- **`README.md`** — this file (how to run the code)
- **`CS 5620 Final Report.pdf`** — written final report (see [Final report](#final-report))

No other application code, API, database, or proprietary assets are included. The report describes the full system the course project is based on (including UI and integration); screenshots and narrative there stand in for code that is not shared here.

---

## Purpose

This document accompanies the submitted folders: what each folder is and how to run it. The **written final report** is included with the submission; see [Final report](#final-report) below for the PDF.

---

## What is in each folder

| Folder | Description |
|--------|-------------|
| **`coachai/`** | **Current** Match Coach work: Node/Wrangler scripts and tooling for the LLM-based coach described in the report. |
| **`old/`** | **Earlier** work: a self-contained Python project (supervised models on match JSON, template-based coach language, optional offline RL, tests). Same approach as in the report’s background / evolution, but **not** identical to the shipped product codebase (which is not submitted). |

---

## Prerequisites

- **`coachai/`:** Node.js (LTS recommended), `npm`, and [Wrangler](https://developers.cloudflare.com/workers/wrangler/) (installed via the `coachai` package).
- **`old/`:** Python 3 and `pip`. No GPU is required for the default workflow.

---

## How to run `coachai/`

Place `coachai/` in the same directory as this file (your submission root), then:

```bash
cd coachai
npm install
npm run dev
```

Use `npm run dev:local` for local Wrangler defaults without `--remote`. More scripts are in `coachai/package.json` (e.g. `npm run coachai:call`, `npm run coachai:help`, `npm run eval`).

**Limitations:** End-to-end use of Workers AI needs **Cloudflare** authentication and bindings I cannot share. If that is unavailable, the **PDF report** includes screenshots and a system description for the demo portion of the assignment.

---

## How to run `old/`

Place `old/` in the same directory as this file (your submission root), then:

```bash
cd old
python3 -m venv venv
source venv/bin/activate
# Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Then follow **`old/README.md`** inside that folder for training (optional), inference (`python3 -m inference.predict …` or `python3 -m nlp.coach …`), and tests (`python3 -m pytest tests/ -q`). No private dataset is required for the default commands.

---

## Demonstration and grading

- **`old/`** should run locally after setup above.
- **`coachai/`** may need Cloudflare access; the **PDF** supplements with figures and explanation where external services are a barrier.

---

## Final report

The written final report for this project: **[CS 5620 Final Report](./CS%205620%20Final%20Report.pdf)** (same directory as this `README.md`).