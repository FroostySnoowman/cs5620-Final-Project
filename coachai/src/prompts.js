const COACHING_SYSTEM = `You are a world-class tennis coach giving mid-match advice to a player.

Rules:
- Respond ONLY with valid JSON — no markdown, no code fences, no extra text.
- The JSON must match this exact schema:
  { "insights": [ { "title": "<short headline>", "detail": "<1-2 sentence explanation>", "urgency": "high" | "medium" | "low" } ] }
- Return exactly 3 insights, ordered by urgency (high first).
- Base every insight on the stats provided — do NOT invent numbers.
- Keep language simple and direct. A 14-year-old player should understand it.
- Focus on what to DO, not what went wrong.`;

const TRAINING_SYSTEM = `You are a world-class tennis coach writing a post-match training plan for a player.

Rules:
- Respond ONLY with valid JSON — no markdown, no code fences, no extra text.
- The JSON must match this exact schema:
  {
    "summary": "<2-3 sentence match overview>",
    "strengths": [ "<strength 1>", "<strength 2>" ],
    "weaknesses": [ "<weakness 1>", "<weakness 2>" ],
    "drills": [ { "name": "<drill name>", "focus": "<what it improves>", "duration": "<suggested time>" } ],
    "focusAreas": [ "<area 1>", "<area 2>" ]
  }
- Return 2-3 strengths, 2-3 weaknesses, 3-4 drills, and 2-3 focus areas.
- Base every recommendation on the stats provided — do NOT invent numbers.
- Keep language simple and direct. A 14-year-old player should understand it.
- Drills should be specific and practical (not vague like "practice more").`;

export function buildCoachingPrompt(stats) {
  const user = `Here are the current mid-match stats for ${stats.focalPlayer} vs ${stats.opponent}.
Points played so far: ${stats.pointsPlayed}.

${stats.focalPlayer}'s stats:
${JSON.stringify(stats.focal, null, 2)}

${stats.opponent}'s stats:
${JSON.stringify(stats.opp, null, 2)}

Recent momentum (last 10 points): ${stats.momentum.pct}% won by ${stats.focalPlayer}.
Rally profile: avg length ${stats.rallyProfile.avg}, short ${stats.rallyProfile.short}%, medium ${stats.rallyProfile.medium}%, long ${stats.rallyProfile.long}%.
${stats.focalPlayer}'s terminal actions: ${JSON.stringify(stats.focalTerminals)}.
Serve streak: current ${stats.focalServeStreak.current}, best ${stats.focalServeStreak.best}.

Give ${stats.focalPlayer} 3 actionable coaching insights for right now.`;

  return [
    { role: "system", content: COACHING_SYSTEM },
    { role: "user", content: user },
  ];
}

export function buildTrainingPrompt(stats) {
  const result = stats.didWin ? "won" : "lost";
  const setLine = stats.sets.map((s) => `${s.focal}-${s.opponent}`).join(", ");

  const user = `Post-match analysis for ${stats.focalPlayer} vs ${stats.opponent}.
Result: ${stats.focalPlayer} ${result}. Sets: ${setLine}. Total points: ${stats.totalPoints}.

${stats.focalPlayer}'s stats:
${JSON.stringify(stats.focal, null, 2)}

${stats.opponent}'s stats:
${JSON.stringify(stats.opp, null, 2)}

Rally profile: avg length ${stats.rallyProfile.avg}, short ${stats.rallyProfile.short}%, medium ${stats.rallyProfile.medium}%, long ${stats.rallyProfile.long}%.

${stats.focalPlayer}'s shot outcomes: ${JSON.stringify(stats.focalTerminals)}.
${stats.opponent}'s shot outcomes: ${JSON.stringify(stats.oppTerminals)}.

Momentum — first 20 points: ${stats.momentum.first20.pct}% won, last 20 points: ${stats.momentum.last20.pct}% won.

Build a training plan for ${stats.focalPlayer} to improve based on this match.`;

  return [
    { role: "system", content: TRAINING_SYSTEM },
    { role: "user", content: user },
  ];
}
