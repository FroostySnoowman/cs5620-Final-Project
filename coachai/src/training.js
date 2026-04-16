import { extractFullMatchStats } from "./analysis.js";
import { buildTrainingPrompt } from "./prompts.js";
import { COACHAI_TEXT_MODEL as MODEL } from "./model.js";

export async function handleTraining(request, env) {
  const body = await request.json();
  const { matchData, focalPlayer } = body;

  if (!matchData || !focalPlayer) {
    return {
      status: 400,
      data: { error: "Request body must include matchData and focalPlayer." },
    };
  }

  const stats = extractFullMatchStats(matchData, focalPlayer);
  const messages = buildTrainingPrompt(stats);

  const aiResponse = await env.AI.run(MODEL, { messages, max_tokens: 2048 });

  const text = (aiResponse.response || "").trim();

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    parsed = {
      summary: "",
      strengths: [],
      weaknesses: [],
      drills: [],
      focusAreas: [],
      rawText: text,
    };
  }

  return {
    status: 200,
    data: { ...parsed, model: MODEL, generatedAt: new Date().toISOString() },
  };
}
