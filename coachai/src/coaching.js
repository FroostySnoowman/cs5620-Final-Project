import { extractMidMatchStats } from "./analysis.js";
import { buildCoachingPrompt } from "./prompts.js";
import { COACHAI_TEXT_MODEL as MODEL } from "./model.js";

export async function handleCoaching(request, env) {
  const body = await request.json();
  const { matchData, focalPlayer } = body;

  if (!matchData || !focalPlayer) {
    return {
      status: 400,
      data: { error: "Request body must include matchData and focalPlayer." },
    };
  }

  const stats = extractMidMatchStats(matchData, focalPlayer);
  const messages = buildCoachingPrompt(stats);

  const aiResponse = await env.AI.run(MODEL, { messages, max_tokens: 1024 });

  const text = (aiResponse.response || "").trim();

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    parsed = { insights: [], rawText: text };
  }

  return {
    status: 200,
    data: { ...parsed, model: MODEL, generatedAt: new Date().toISOString() },
  };
}
