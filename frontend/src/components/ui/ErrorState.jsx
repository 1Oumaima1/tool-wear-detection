export default function ErrorState({ error, onRetry }) {
  const detail =
    error?.response?.data?.detail ||
    error?.message ||
    "Le backend n'a pas répondu.";

  return (
    <div className="border border-status-critical/20 bg-status-criticalBg rounded-card p-4 text-sm">
      <p className="text-status-critical font-medium mb-1">Impossible de charger les données</p>
      <p className="text-ink-mid text-xs">{String(detail)}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 text-xs font-medium text-brand-600 hover:underline">
          Réessayer
        </button>
      )}
    </div>
  );
}
