function pct(numerator, denominator) {
  if (!denominator) return 0;
  return Math.round((numerator / denominator) * 100);
}

function safeDiv(a, b) {
  return b ? +(a / b).toFixed(2) : 0;
}

function momentum(history, focalPlayer, windowSize = 10) {
  const recent = history.slice(-windowSize);
  if (!recent.length) return { pointsWon: 0, pointsPlayed: 0, pct: 0 };
  const won = recent.filter((p) => p.pointWinnerId === focalPlayer).length;
  return { pointsWon: won, pointsPlayed: recent.length, pct: pct(won, recent.length) };
}

function rallyProfile(history) {
  if (!history.length) return { avg: 0, short: 0, medium: 0, long: 0 };
  const lengths = history.map((p) => p.rallyLength || 1);
  const avg = safeDiv(lengths.reduce((s, l) => s + l, 0), lengths.length);
  const short = pct(lengths.filter((l) => l <= 4).length, lengths.length);
  const medium = pct(lengths.filter((l) => l > 4 && l <= 8).length, lengths.length);
  const long = pct(lengths.filter((l) => l > 8).length, lengths.length);
  return { avg, short, medium, long };
}

function terminalActions(history, player) {
  const totals = { aces: 0, doubleFaults: 0, winners: 0, unforcedErrors: 0, forcedErrors: 0 };
  for (const point of history) {
    const actions = point.actions || [];
    if (!actions.length) continue;
    const terminal = actions[actions.length - 1];
    if (!terminal) continue;
    const type = (terminal.type || "").toUpperCase();
    const actor = terminal.actorId;

    if (actor === player) {
      if (type === "ACE") totals.aces++;
      if (type === "DOUBLE_FAULT" || type === "DOUBLE FAULT") totals.doubleFaults++;
      if (type === "WINNER") totals.winners++;
      if (type === "UNFORCED ERROR" || type === "UNFORCED_ERROR") totals.unforcedErrors++;
    } else {
      if (type === "FORCED ERROR" || type === "FORCED_ERROR") totals.forcedErrors++;
    }
  }
  return totals;
}

function serveStreak(history, player) {
  let current = 0;
  let best = 0;
  for (const point of history) {
    if (point.serverId !== player) continue;
    if (point.pointWinnerId === player) {
      current++;
      if (current > best) best = current;
    } else {
      current = 0;
    }
  }
  return { current, best };
}

function playerSummary(playerStats) {
  const s = playerStats.serve || {};
  const r = playerStats.return || {};
  const ra = playerStats.rally || {};
  const m = playerStats.individualMatch || {};

  return {
    serve: {
      aces: s.aces || 0,
      doubleFaults: s.doubleFaults || 0,
      firstServePct: pct(s.firstServeIn, s.firstServeAttempted),
      firstServeWinPct: pct(s.firstServePointsWon, s.firstServePointsPlayed),
      secondServeWinPct: pct(s.secondServePointsWon, s.secondServePointsPlayed),
      servicePointsWonPct: pct(s.servicePointsWon, s.servicePointsPlayed),
      breakPointsSaved: s.breakPointsSaved || 0,
      breakPointsFaced: s.breakPointsFaced || 0,
      breakPointSavePct: pct(s.breakPointsSaved, s.breakPointsFaced),
    },
    return: {
      returnPointsWonPct: pct(r.returnPointsWon, r.returnPointsPlayed),
      firstReturnWinPct: pct(r.firstServeReturnPointsWon, r.firstServeReturnPointsPlayed),
      secondReturnWinPct: pct(r.secondServeReturnPointsWon, r.secondServeReturnPointsPlayed),
      breakPointsConverted: r.breakPointsConverted || 0,
      breakPointOpportunities: r.breakPointOpportunities || 0,
      breakPointConversionPct: pct(r.breakPointsConverted, r.breakPointOpportunities),
      returnErrors: (r.returnForcedErrors || 0) + (r.returnUnforcedErrors || 0),
    },
    rally: {
      winners: ra.winners || 0,
      unforcedErrors: ra.unforcedErrors || 0,
      forcedErrors: ra.forcedErrors || 0,
      winnerToErrorRatio: safeDiv(ra.winners || 0, (ra.unforcedErrors || 0) + (ra.forcedErrors || 0)),
      netPointsWon: ra.netPointsWon || 0,
      netPointsAttempted: ra.netPointsAttempted || 0,
      netWinPct: pct(ra.netPointsWon, ra.netPointsAttempted),
      avgRallyLength: safeDiv(ra.totalRallyLength, ra.rallyCount),
    },
    match: {
      pointsWon: m.pointsWon || 0,
      pointsPlayed: m.pointsPlayed || 0,
      pointsWonPct: pct(m.pointsWon, m.pointsPlayed),
      serviceGamesWon: m.serviceGamesWon || 0,
      serviceGamesPlayed: m.serviceGamesPlayed || 0,
      longestPointStreak: m.longestPointStreak || 0,
    },
  };
}

export function extractMidMatchStats(matchData, focalPlayer) {
  const playerNames = Object.keys(matchData.players || {});
  const opponent = playerNames.find((n) => n !== focalPlayer) || playerNames[1] || "Opponent";
  const history = matchData.history || [];

  const focalAgg = matchData.players?.[focalPlayer];
  const oppAgg = matchData.players?.[opponent];

  return {
    focalPlayer,
    opponent,
    pointsPlayed: history.length,
    focal: focalAgg ? playerSummary(focalAgg) : null,
    opp: oppAgg ? playerSummary(oppAgg) : null,
    momentum: momentum(history, focalPlayer),
    rallyProfile: rallyProfile(history),
    focalTerminals: terminalActions(history, focalPlayer),
    focalServeStreak: serveStreak(history, focalPlayer),
  };
}

export function extractFullMatchStats(matchData, focalPlayer) {
  const playerNames = Object.keys(matchData.players || {});
  const opponent = playerNames.find((n) => n !== focalPlayer) || playerNames[1] || "Opponent";
  const history = matchData.history || [];

  const focalAgg = matchData.players?.[focalPlayer];
  const oppAgg = matchData.players?.[opponent];

  const sets = (matchData.sets || []).map((set) => ({
    focal: set.games?.[focalPlayer] ?? 0,
    opponent: set.games?.[opponent] ?? 0,
    tiebreak: set.tiebreak ?? null,
  }));

  return {
    focalPlayer,
    opponent,
    matchWinner: matchData.matchWinner || null,
    didWin: matchData.matchWinner === focalPlayer,
    sets,
    totalPoints: history.length,
    focal: focalAgg ? playerSummary(focalAgg) : null,
    opp: oppAgg ? playerSummary(oppAgg) : null,
    rallyProfile: rallyProfile(history),
    focalTerminals: terminalActions(history, focalPlayer),
    oppTerminals: terminalActions(history, opponent),
    focalServeStreak: serveStreak(history, focalPlayer),
    oppServeStreak: serveStreak(history, opponent),
    momentum: {
      first20: momentum(history.slice(0, 20), focalPlayer, 20),
      last20: momentum(history, focalPlayer, 20),
    },
  };
}
