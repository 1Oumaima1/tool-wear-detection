import { SEVERITY_META, severityFromClass } from "./statusMeta";

export default function WearLevelBar({ predictedClass, wearLevel }) {
  const meta = SEVERITY_META[severityFromClass(predictedClass)] || SEVERITY_META.normal;
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-ink-mid text-xs">Niveau d'usure</span>
        <span className={`text-sm font-semibold ${meta.text}`}>{wearLevel}%</span>
      </div>
      <div className="h-2 bg-surface-hover rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${meta.dot}`}
          style={{ width: `${wearLevel}%`, transition: "width 0.4s ease" }}
        />
      </div>
    </div>
  );
}
