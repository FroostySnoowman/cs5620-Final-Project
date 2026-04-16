export const PRESENTATION_RUBRIC = {
  title: "Project presentation (typical 10 pt breakdown)",
  criteria: [
    {
      id: "problem",
      label: "Statement of the problem",
      points: 2,
      prompts: [
        "Motivate the work: why is raw match data hard to turn into strategy?",
        "Who struggles (e.g. club players without a coach courtside)?",
      ],
    },
    {
      id: "related_work",
      label: "Related work",
      points: 2,
      prompts: [
        "Name 1–2 similar systems (commercial apps, research tutors, generic ChatGPT-on-stats).",
        "What is different or better here (on-device flow, structured stats → constrained JSON, Workers AI, etc.)?",
      ],
    },
    {
      id: "skills",
      label: "Skills / knowledge you address",
      points: 2,
      prompts: [
        "Declarative: reading stats (serve %, break points, rally length).",
        "Procedural: what to try next (target weakness, change risk).",
        "Metacognitive: reflecting after the match (training plan).",
      ],
    },
    {
      id: "interaction",
      label: "How learners interact",
      points: 2,
      prompts: [
        "Logging points → milestone banner → opening coach sheet (choices + timing).",
        "Errors: sparse logging, wrong player, skipping advanced actions — how does the tutor degrade?",
        "Post-match: open training plan after completion.",
      ],
    },
    {
      id: "ai_techniques",
      label: "AI techniques used",
      points: 2,
      prompts: [
        "Rule-based feature extraction from match_stats JSON (inputs to the model).",
        "LLM with strict JSON schema (Workers AI) + caching to control cost.",
        "Show one screenshot: extracted snippet + model output side by side.",
      ],
    },
  ],
};

function isNonEmptyString(x) {
  return typeof x === "string" && x.trim().length > 0;
}

function inRange(s, min, max) {
  if (!isNonEmptyString(s)) return false;
  const n = s.trim().length;
  return n >= min && n <= max;
}

export function evaluateCoachingPayload(body) {
  const checks = [];
  const add = (id, label, pass, detail) => {
    checks.push({ id, label, pass: !!pass, ...(detail ? { detail } : {}) });
  };

  if (!body || typeof body !== "object") {
    add("shape", "Body is a JSON object", false, "Expected object.");
    return { checks, passed: 0, total: checks.length };
  }

  const insights = body.insights;
  add("insights_array", "`insights` is an array", Array.isArray(insights));
  add(
    "insights_count",
    "Exactly 3 insights (matches product contract)",
    Array.isArray(insights) && insights.length === 3,
    Array.isArray(insights) ? `length=${insights.length}` : undefined
  );

  if (Array.isArray(insights)) {
    const titles = [];
    insights.forEach((ins, i) => {
      const p = ins && typeof ins === "object" ? ins : {};
      add(`i${i}_title`, `Insight ${i + 1} has title`, inRange(p.title, 4, 120));
      add(`i${i}_detail`, `Insight ${i + 1} has detail (20–600 chars)`, inRange(p.detail, 20, 600));
      const u = String(p.urgency || "").toLowerCase();
      add(`i${i}_urgency`, `Insight ${i + 1} urgency is high|medium|low`, ["high", "medium", "low"].includes(u));
      if (isNonEmptyString(p.title)) titles.push(String(p.title).trim().toLowerCase());
    });
    const uniq = new Set(titles);
    add("titles_distinct", "Insight titles are not all identical", titles.length < 2 || uniq.size > 1);
  }

  const passed = checks.filter((c) => c.pass).length;
  return { checks, passed, total: checks.length };
}

export function evaluateTrainingPayload(body) {
  const checks = [];
  const add = (id, label, pass, detail) => {
    checks.push({ id, label, pass: !!pass, ...(detail ? { detail } : {}) });
  };

  if (!body || typeof body !== "object") {
    add("shape", "Body is a JSON object", false);
    return { checks, passed: 0, total: checks.length };
  }

  add("summary", "Summary present (20–1200 chars)", inRange(body.summary, 20, 1200));

  const strengths = body.strengths;
  add(
    "strengths",
    "2–5 strengths, each ≥5 chars",
    Array.isArray(strengths) &&
      strengths.length >= 2 &&
      strengths.length <= 5 &&
      strengths.every((s) => isNonEmptyString(s) && String(s).trim().length >= 5)
  );

  const weaknesses = body.weaknesses;
  add(
    "weaknesses",
    "2–5 weaknesses, each ≥5 chars",
    Array.isArray(weaknesses) &&
      weaknesses.length >= 2 &&
      weaknesses.length <= 5 &&
      weaknesses.every((s) => isNonEmptyString(s) && String(s).trim().length >= 5)
  );

  const drills = body.drills;
  const drillsOk =
    Array.isArray(drills) &&
    drills.length >= 3 &&
    drills.length <= 6 &&
    drills.every(
      (d) =>
        d &&
        typeof d === "object" &&
        isNonEmptyString(d.name) &&
        isNonEmptyString(d.focus) &&
        isNonEmptyString(d.duration)
    );
  add("drills", "3–6 drills with name, focus, duration", drillsOk);

  const focus = body.focusAreas;
  add(
    "focusAreas",
    "2–5 focus areas",
    Array.isArray(focus) && focus.length >= 2 && focus.length <= 5 && focus.every((s) => isNonEmptyString(s))
  );

  const passed = checks.filter((c) => c.pass).length;
  return { checks, passed, total: checks.length };
}

export function evaluateCoachOutputs(payload) {
  const out = {
    presentationRubric: PRESENTATION_RUBRIC,
    coaching: null,
    training: null,
    summary: "",
  };

  if (payload.coaching != null) {
    out.coaching = evaluateCoachingPayload(payload.coaching);
  }
  if (payload.training != null) {
    out.training = evaluateTrainingPayload(payload.training);
  }

  const parts = [];
  if (out.coaching) {
    parts.push(`Coaching checks: ${out.coaching.passed}/${out.coaching.total} passed.`);
  }
  if (out.training) {
    parts.push(`Training checks: ${out.training.passed}/${out.training.total} passed.`);
  }
  out.summary = parts.join(" ") || "No coaching or training payload provided.";
  return out;
}
