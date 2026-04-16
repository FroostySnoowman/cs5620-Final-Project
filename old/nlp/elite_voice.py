"""
Calm, precise elite-team coach tone (court imagery, unhurried authority).

Used for multi-slot templates and optional synonym substitution (local LM).
"""

from __future__ import annotations

# Openers / cadence (slot fillers) — keep second person, no ML jargon
ELITE_OPENERS = (
    "Quiet hands, clear intention—",
    "The geometry of the court is on your side when",
    "I'd keep the feet busy and the mind still:",
    "Under pressure, the cleanest path is usually",
    "Let the ball come to you, then",
    "Rhythm first, damage second—",
    "You don't need hero shots; you need",
    "Trust the work you've put in—",
    "Small margins decide these matches, so",
    "When you own the middle,",
    "Depth buys you time; use it to",
    "Make them solve problems on every shot—",
    "Clean contact, simple targets:",
    "The scoreboard follows execution, not the other way around—",
    "Stay patient in the shoulders, sharp in the feet:",
    "Read the ball early, commit late—",
    "Win the neutral before you hunt the finish—",
    "Keep the ball heavy through the court—",
    "If you control the first two shots,",
    "Let patterns breathe; don't force the same look twice—",
    "Take care of your serve games like they're sacred—",
    "On return, steal time without gambling—",
    "Move them before you hurt them—",
    "The backhand lane can be a runway or a trap—choose which—",
    "Volleys reward calm hands, not rushed frames—",
    "Slice isn't defensive if it buys you space—",
    "High balls to the shoulder are a test—pass it—",
    "Don't rush the net; earn it—",
    "Tiebreak energy is just focus in shorter bursts—",
)

ELITE_BRIDGES = (
    "what the sheet is telling us is",
    "the clean read here is",
    "I'd want you walking out believing",
    "the matchup leans toward",
    "your edge shows up when",
    "the numbers reward",
    "I'd script the point so you",
    "the simplest winning idea is",
    "I'd emphasize",
    "the priority is",
    "lock in on",
    "don't overthink—just",
    "trust the trend:",
    "lean into",
    "keep steering traffic toward",
)

ELITE_CADENCES = (
    "and stay with it across sets.",
    "and let the rally tell you when to pull the trigger.",
    "one point, one plan.",
    "that's the match within the match.",
    "keep that theme when it gets loud.",
    "discipline beats doubt.",
    "clean targets, full commitment.",
    "make them earn every cheap point.",
    "no free real estate.",
    "breathe, reset, repeat.",
    "simple wins.",
    "trust the legs when the point stretches.",
    "own your patterns.",
)

# Momentum / flow hooks (paired with narrative context buckets)
HOOK_HOT = (
    "You've been finding answers in the recent points—ride that clarity.",
    "Momentum is a quiet thing; yours has been building in the exchanges we can see.",
    "When the ball is listening, keep the message simple.",
)

HOOK_COLD = (
    "The last stretch has been sticky—treat it as information, not verdict.",
    "If the points feel tight, go back to first principles: spacing and timing.",
    "Form dips; fundamentals don't—lean on what travels.",
)

HOOK_NEUTRAL = (
    "The match has been a push-and-pull—control what you can on the next ball.",
    "Neither side owns the story yet; execution will tip it.",
    "Stay even in the head, sharp in the feet.",
)

HOOK_SERVE_HEAVY = (
    "They've leaned on your service games—make serves first serves, seconds unpredictable.",
)

HOOK_RETURN_CHANCEY = (
    "Break chances matter—tighten targets when the door opens.",
)

HOOK_SHORT_RALLY_SHAPE = (
    "Most points are short here—first-strike discipline is the real coach.",
)

# Synonyms for local LM substitution (same intent, no new facts)
SYNONYMS: dict[str, tuple[str, ...]] = {
    "pressure": ("stress", "heat", "load", "strain"),
    "depth": ("length", "weight through the court", "deep targets"),
    "patience": ("composure", "poise", "calm"),
    "simple": ("clean", "straightforward", "plain"),
    "trust": ("lean on", "believe in", "back"),
    "patterns": ("looks", "sequences", "shapes"),
    "margin": ("buffer", "cushion", "room"),
    "rhythm": ("tempo", "timing", "cadence"),
    "court": ("playing field", "rectangle", "court"),
    "neutral": ("middle exchanges", "neutral balls", "rally balls"),
}
