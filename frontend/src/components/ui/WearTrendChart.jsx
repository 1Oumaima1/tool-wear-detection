import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from "recharts";

const tooltipStyle = {
  backgroundColor: "#FFFFFF",
  border: "1px solid #E5E9F0",
  borderRadius: 8,
  fontSize: 12,
  boxShadow: "0 4px 12px rgba(15,23,42,0.08)",
};

export default function WearTrendChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <CartesianGrid stroke="#EEF2F7" vertical={false} />
        <XAxis dataKey="time" stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
        <YAxis
          stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false}
          domain={[0, 100]} tickFormatter={(v) => `${v}%`}
        />
        <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v}%`, "Niveau d'usure"]} />
        <ReferenceLine y={66} stroke="#E11D48" strokeDasharray="4 4" strokeWidth={1.5} />
        <ReferenceLine y={33} stroke="#D97706" strokeDasharray="4 4" strokeWidth={1.5} />
        <Line type="monotone" dataKey="wearLevel" stroke="#2563EB" strokeWidth={2.5} dot={{ r: 3, fill: "#2563EB" }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
