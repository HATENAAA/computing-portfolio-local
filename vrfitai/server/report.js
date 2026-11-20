export function trainingReport(rows) {
  const summary = { sessions: rows.length, seconds: 0, hits: 0 };
  const programs = {};
  for (const row of rows) {
    summary.seconds += row.seconds; summary.hits += row.hits;
    const p = programs[row.program] ||= { sessions: 0, seconds: 0, hits: 0 };
    p.sessions++; p.seconds += row.seconds; p.hits += row.hits;
  }
  return { version: 1, timezone: 'UTC', summary, programs, records: rows,
    definitions: { seconds: 'active time excluding pause', hits: 'target interactions, not exercise repetitions',
      scope: 'Interaction training log; no pose score, heart rate or energy expenditure inferred.' } };
}
