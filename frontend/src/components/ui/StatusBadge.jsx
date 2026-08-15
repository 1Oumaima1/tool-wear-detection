import { SEVERITY_META, severityFromClass } from "./statusMeta";

/** Pastille colorée pleine (ex: CRITIQUE / WARNING / NORMAL). `label` permet de
 * surcharger le texte affiché (ex: "RÉSOLU") tout en gardant le style d'une sévérité. */
export function StatusPill({ predictedClass, severity, label }) {
  const key = severity || severityFromClass(predictedClass);
  const meta = SEVERITY_META[key] || SEVERITY_META.normal;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${meta.bg} ${meta.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
      {label || meta.label}
    </span>
  );
}

/** Texte coloré en gras, sans fond (utilisé pour la classe brute sharp/used/dulled). */
export function ClassText({ predictedClass }) {
  const meta = SEVERITY_META[severityFromClass(predictedClass)] || SEVERITY_META.normal;
  return <span className={`font-semibold uppercase text-sm ${meta.text}`}>{predictedClass}</span>;
}
