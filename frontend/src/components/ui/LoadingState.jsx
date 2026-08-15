import { LuLoaderCircle } from "react-icons/lu";

export default function LoadingState({ label = "Chargement…" }) {
  return (
    <div className="flex items-center gap-2 text-ink-mid py-10 justify-center text-sm">
      <LuLoaderCircle className="animate-spin text-brand-600" size={16} />
      {label}
    </div>
  );
}
