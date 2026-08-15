export default function StatCard({ icon: Icon, label, value, sub, accent = "text-ink-hi", iconBg = "bg-brand-50", iconColor = "text-brand-600" }) {
  return (
    <div className="bg-surface-card border border-surface-border rounded-card p-4 shadow-card">
      <div className="flex items-center gap-3 mb-3">
        {Icon && (
          <span className={`w-9 h-9 rounded-lg flex items-center justify-center ${iconBg}`}>
            <Icon size={18} className={iconColor} />
          </span>
        )}
        <p className="text-ink-mid text-xs font-medium">{label}</p>
      </div>
      <p className={`text-2xl font-semibold ${accent}`}>{value}</p>
      {sub && <p className="text-ink-dim text-xs mt-1">{sub}</p>}
    </div>
  );
}
