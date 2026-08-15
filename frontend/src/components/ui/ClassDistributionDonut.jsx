import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

const COLORS = { sharp: "#16A34A", used: "#D97706", dulled: "#E11D48" };
const LABELS = { sharp: "Sharp (Normal)", used: "Used (Usure modérée)", dulled: "Dulled (Usure élevée)" };

export default function ClassDistributionDonut({ distribution }) {
  const total = Object.values(distribution).reduce((a, b) => a + b, 0);
  const data = Object.entries(distribution)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value }));

  return (
    <div className="flex items-center gap-6">
      <div className="relative w-36 h-36 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={42} outerRadius={64} paddingAngle={2}>
              {data.map((d) => (
                <Cell key={d.name} fill={COLORS[d.name]} stroke="none" />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-xl font-bold text-ink-hi">{total}</span>
          <span className="text-[10px] text-ink-dim">Total</span>
        </div>
      </div>
      <div className="space-y-2">
        {Object.entries(distribution).map(([cls, count]) => (
          <div key={cls} className="flex items-center gap-2 text-sm">
            <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: COLORS[cls] }} />
            <span className="text-ink-mid">{LABELS[cls]}</span>
            <span className="text-ink-hi font-medium">
              {count} ({total ? Math.round((count / total) * 100) : 0}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
