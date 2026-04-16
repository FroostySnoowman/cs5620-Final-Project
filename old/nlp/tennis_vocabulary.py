"""
Tennis-specific word pools for combinatorial coach lines (no LLM).

Large finite vocabulary; combined with templates yields enormous variety.
"""

# Intros / transitions
OPENERS = (
    "Look,",
    "Remember:",
    "Bottom line—",
    "Here's the read—",
    "My take:",
    "Straight talk:",
    "On paper,",
    "What jumps out:",
    "If I'm you,",
    "Court sense says",
    "The story here is",
    "Pattern-wise,",
    "Tactically,",
    "Matchup-wise,",
    "Against this opponent,",
    "Film and numbers agree:",
    "From the chair,",
    "In this matchup,",
    "The scouting line is",
    "What the sheet says:",
    "No secrets here—",
    "Clean read:",
    "Honest note:",
    "Priority cue:",
    "First principle:",
    "Big picture,",
    "Micro-detail:",
    "Serve-return math says",
    "Transition game says",
    "Pressure points favor",
    "Neutral-ball edge goes to",
    "Shot-quality trends show",
    "Winner/error deltas hint",
    "Court geometry favors",
    "Risk/reward tilts toward",
    "Execution under pressure:",
    "When it gets loud,",
    "Late in sets,",
    "On breakpoint-ish balls,",
)

# Verbs / actions
PRESSURE_VERBS = (
    "pressure",
    "stress-test",
    "probe",
    "attack",
    "target",
    "lean on",
    "tilt patterns toward",
    "make them defend",
    "open up",
    "exploit",
    "chip away at",
    "overload",
    "jam",
    "pull wide",
    "lift to",
    "drag into",
    "compress time against",
    "deny pace to",
    "invite errors from",
    "squeeze",
    "own the middle against",
    "take the high ground against",
)

DEPTH_WORDS = (
    "depth",
    "length",
    "heavy balls",
    "deep targets",
    "court position",
    "margin over the net",
    "shape and height",
)

NET_WORDS = (
    "the front of the court",
    "net rushes",
    "approach shots",
    "transition balls",
    "volley finishes",
    "put-aways",
)

SERVE_WORDS = (
    "first serves",
    "second serves",
    "serve placement",
    "serve-plus-one",
    "kick locations",
    "wide T serves",
    "body serves",
)

RETURN_WORDS = (
    "return depth",
    "block returns",
    "chip returns",
    "neutral returns",
    "return aggression",
    "second-ball targets",
)

RALLY_WORDS = (
    "rally tolerance",
    "extended exchanges",
    "cat-and-mouse points",
    "grind-mode rallies",
    "short first-strike points",
    "baseline tug-of-war",
    "four-shot sequences",
    "longer patterns",
    "transition-heavy points",
    "serve-plus-one races",
)

WING_WORDS = (
    "the backhand wing",
    "the forehand side",
    "the run-around forehand",
    "the backhand slice lane",
    "the high backhand",
)

CLOSING_FRAGS = (
    "and stay disciplined on execution.",
    "without gifting cheap errors.",
    "and let the scoreboard follow.",
    "one ball at a time.",
    "and trust your legs when it gets physical.",
    "and keep your patterns unpredictable.",
    "and breathe between points.",
    "and reset after every rally.",
    "and track the ball early.",
    "and keep your feet active.",
    "and stay light on your toes.",
    "and own your spacing.",
    "and stay sharp on the first two shots.",
    "and build the point in layers.",
    "and avoid the hero ball early.",
    "and play the percentages.",
    "and stay committed through contact.",
)

# Extra pools for more combinations
MOOD = (
    "quietly",
    "consistently",
    "relentlessly",
    "patiently",
    "smartly",
    "calmly",
    "aggressively when it's on",
)

OPP_PRESSURE = (
    "move them",
    "pin them",
    "stretch them",
    "rotate them",
    "deny rhythm to",
    "side-to-side them",
    "empty their legs",
    "force extra steps from",
)
