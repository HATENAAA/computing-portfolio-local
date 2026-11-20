// Subscribe per XR session; never auto-resume a session after loss of visibility.
export function bindXRVisibility(session, pause) {
  const listener = () => { if (session.visibilityState !== 'visible') pause(); };
  session.addEventListener('visibilitychange', listener);
  listener();
  return () => session.removeEventListener('visibilitychange', listener);
}
export function xrAction(data) {
  if (data.exit) return 'exit';
  if (data.finish) return 'finish';
  if (data.pause) return 'toggle';
  return 'hit';
}
