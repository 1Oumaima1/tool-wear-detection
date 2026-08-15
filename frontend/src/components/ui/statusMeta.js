export const CLASS_TO_SEVERITY = {
  sharp: "normal",
  used: "warning",
  dulled: "critical",
};

export const SEVERITY_META = {
  normal: { label: "NORMAL", text: "text-status-normal", bg: "bg-status-normalBg", dot: "bg-status-normal" },
  warning: { label: "WARNING", text: "text-status-warning", bg: "bg-status-warningBg", dot: "bg-status-warning" },
  critical: { label: "CRITIQUE", text: "text-status-critical", bg: "bg-status-criticalBg", dot: "bg-status-critical" },
};

export function severityFromClass(predictedClass) {
  return CLASS_TO_SEVERITY[predictedClass] || "normal";
}

export function wearLevelFromPrediction(predictedClass, confidence) {
  // Le modèle ne produit que 3 classes discrètes (pas de score continu
  // d'usure). Ce "niveau d'usure %" est une valeur dérivée à but visuel :
  // chaque classe occupe un tiers de l'échelle, positionnée dans ce tiers
  // proportionnellement à la confiance du modèle.
  const base = { sharp: 0, used: 33, dulled: 66 }[predictedClass] ?? 0;
  return Math.min(100, Math.round(base + confidence * 33));
}
