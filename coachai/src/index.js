import { handleCoaching } from "./coaching.js";
import { handleTraining } from "./training.js";
import { evaluateCoachOutputs, PRESENTATION_RUBRIC } from "./eval.js";

const ALLOWED_ORIGINS = new Set([
  "http://localhost:5173",
  "http://127.0.0.1:5173",
  "http://localhost:5005",
  "http://127.0.0.1:5005",
  "http://localhost:8081",
  "http://127.0.0.1:8081",
  "http://localhost:8787",
  "http://localhost:8790",
  "http://127.0.0.1:8790",
  "https://mybreakpoint.app",
  "http://mybreakpoint.app",
  "https://api.mybreakpoint.app",
  "http://api.mybreakpoint.app",
  "https://mybreakpoint.pages.dev",
  "http://mybreakpoint.pages.dev",
]);

function corsHeaders(request) {
  const origin = request.headers.get("Origin") || "";
  const headers = new Headers();

  if (ALLOWED_ORIGINS.has(origin)) {
    headers.set("Access-Control-Allow-Origin", origin);
    headers.set("Access-Control-Allow-Credentials", "true");
  }

  headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization");
  headers.set("Access-Control-Expose-Headers", "Content-Type");
  return headers;
}

function jsonResponse(request, body, status = 200) {
  const headers = corsHeaders(request);
  headers.set("Content-Type", "application/json");
  return new Response(JSON.stringify(body), { status, headers });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(request) });
    }

    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    if (path === "/health" && request.method === "GET") {
      return jsonResponse(request, { status: "ok", service: "coachai" });
    }

    if (path === "/eval" && request.method === "GET") {
      return jsonResponse(request, {
        service: "coachai",
        presentationRubric: PRESENTATION_RUBRIC,
        usage: {
          post:
            "POST /eval — body may be { coaching, training } or a raw coaching JSON (with insights[]) / training JSON (with summary + drills[]). Returns heuristic checks + presentation rubric.",
          exampleCoaching: { insights: [], model: "@cf/..." },
          exampleTraining: { summary: "", strengths: [], weaknesses: [], drills: [], focusAreas: [] },
        },
      });
    }

    if (path === "/eval" && request.method === "POST") {
      try {
        const raw = await request.text();
        const body = raw ? JSON.parse(raw) : {};
        const coaching =
          body.coaching != null ? body.coaching : Array.isArray(body.insights) ? body : undefined;
        const training =
          body.training != null
            ? body.training
            : typeof body.summary === "string" && Array.isArray(body.drills)
              ? body
              : undefined;
        const result = evaluateCoachOutputs({ coaching, training });
        return jsonResponse(request, result, 200);
      } catch (err) {
        return jsonResponse(request, { error: err.message || "Invalid JSON body." }, 400);
      }
    }

    if (path === "/coaching" && request.method === "POST") {
      try {
        const result = await handleCoaching(request, env);
        return jsonResponse(request, result.data, result.status);
      } catch (err) {
        return jsonResponse(request, { error: err.message || "Coaching analysis failed." }, 500);
      }
    }

    if (path === "/training" && request.method === "POST") {
      try {
        const result = await handleTraining(request, env);
        return jsonResponse(request, result.data, result.status);
      } catch (err) {
        return jsonResponse(request, { error: err.message || "Training analysis failed." }, 500);
      }
    }

    return jsonResponse(request, { error: "Not found." }, 404);
  },
};
