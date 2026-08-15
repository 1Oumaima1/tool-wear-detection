export default function EmptyState({ title, action }) {
  return (
    <div className="border border-dashed border-surface-border rounded-card p-8 text-center bg-surface-card">
      <p className="text-ink-mid text-sm">{title}</p>
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
