"""
Normalized action vocabulary for point history (uppercase strings after strip).

Terminal / outcome-like types commonly appear as the last meaningful action.
Serve chain types describe the serve portion of the point, not rally outcome.
"""

# Serve-phase action types (not used as rally terminal)
SERVE_PHASE_TYPES = frozenset(
    {
        "FIRST_SERVE_FAULT",
        "SECOND_SERVE_FAULT",
        "FIRST_IN",
        "SECOND_IN",
        "LET",
    }
)

# Rally outcome tokens (subset; extend as new data appears)
OUTCOME_TYPES = frozenset(
    {
        "ACE",
        "DOUBLE FAULT",
        "WINNER",
        "FORCED ERROR",
        "UNFORCED ERROR",
        "RETURN_FORCED_ERROR",
        "RETURN_UNFORCED_ERROR",
    }
)

# Tactic class indices (must match training / inference)
TACTIC_AGGRESSIVE = 0
TACTIC_NEUTRAL = 1
TACTIC_APPROACH_NET = 2
TACTIC_EXTEND_RALLY = 3

NUM_TACTICS = 4

TACTIC_NAMES = {
    TACTIC_AGGRESSIVE: "aggressive",
    TACTIC_NEUTRAL: "neutral",
    TACTIC_APPROACH_NET: "approach_net",
    TACTIC_EXTEND_RALLY: "extend_rally",
}

LONG_RALLY_THRESHOLD = 8
SHORT_RALLY_THRESHOLD = 2
