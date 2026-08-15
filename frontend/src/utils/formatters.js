export function formatElapsed(sinceMs) {
  if (!sinceMs) return "—";
  const totalSeconds = Math.max(0, Math.floor((Date.now() - sinceMs) / 1000));
  const h = String(Math.floor(totalSeconds / 3600)).padStart(2, "0");
  const m = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, "0");
  const s = String(totalSeconds % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}
