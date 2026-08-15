import { useEffect, useState, useCallback, useMemo } from "react";
import { LuDownload } from "react-icons/lu";
import DashboardLayout from "../components/layout/DashboardLayout";
import { StatusPill, ClassText } from "../components/ui/StatusBadge";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import EmptyState from "../components/ui/EmptyState";
import { listPredictions } from "../api/predictions";
import { API_ORIGIN } from "../api/axiosClient";
import { severityFromClass, wearLevelFromPrediction } from "../components/ui/statusMeta";

const PAGE_SIZE = 8;

function toDateInputValue(d) {
  return d.toISOString().slice(0, 10);
}

export default function History() {
  const [predictions, setPredictions] = useState([]);
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return toDateInputValue(d);
  });
  const [dateTo, setDateTo] = useState(() => toDateInputValue(new Date()));
  const [classFilter, setClassFilter] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        limit: 500,
        date_from: new Date(`${dateFrom}T00:00:00`).toISOString(),
        date_to: new Date(`${dateTo}T23:59:59`).toISOString(),
      };
      if (classFilter) params.predicted_class = classFilter;
      setPredictions(await listPredictions(params));
      setPage(1);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo, classFilter]);

  useEffect(() => { load(); }, [load]);

  const totalPages = Math.max(1, Math.ceil(predictions.length / PAGE_SIZE));
  const pageItems = predictions.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const csvContent = useMemo(() => {
    const header = ["id", "date_heure", "machine_id", "tool_id", "prediction", "confiance", "niveau_usure_pct", "source"];
    const rows = predictions.map((p) => [
      p.id,
      new Date(p.created_at).toLocaleString("fr-FR"),
      p.machine_id,
      p.tool_id,
      p.predicted_class,
      (p.confidence * 100).toFixed(1),
      wearLevelFromPrediction(p.predicted_class, p.confidence),
      p.source,
    ]);
    return [header, ...rows].map((r) => r.join(",")).join("\n");
  }, [predictions]);

  function handleExportCSV() {
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `inspection_history_${dateFrom}_${dateTo}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <DashboardLayout
      title="Historique des inspections"
      subtitle="Consultez toutes les inspections effectuées"
      topbarChildren={
        <button
          onClick={handleExportCSV}
          disabled={predictions.length === 0}
          className="flex items-center gap-2 bg-brand-600 text-white rounded-lg px-3.5 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-40"
        >
          <LuDownload size={15} /> Exporter CSV
        </button>
      }
    >
      <div className="bg-surface-card border border-surface-border rounded-card shadow-card overflow-hidden">
        <div className="flex flex-wrap items-center gap-3 p-4 border-b border-surface-border">
          <div className="flex items-center gap-2 text-sm">
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
              className="bg-white border border-surface-border rounded-lg px-2.5 py-1.5 text-ink-hi" />
            <span className="text-ink-dim">→</span>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
              className="bg-white border border-surface-border rounded-lg px-2.5 py-1.5 text-ink-hi" />
          </div>
          <select
            value={classFilter}
            onChange={(e) => setClassFilter(e.target.value)}
            className="bg-white border border-surface-border rounded-lg px-3 py-1.5 text-sm text-ink-hi"
          >
            <option value="">Toutes les classes</option>
            <option value="sharp">Sharp</option>
            <option value="used">Used</option>
            <option value="dulled">Dulled</option>
          </select>
        </div>

        {loading && <LoadingState label="Chargement de l'historique…" />}
        {error && <div className="p-4"><ErrorState error={error} onRetry={load} /></div>}

        {!loading && !error && (
          predictions.length === 0 ? (
            <div className="p-6"><EmptyState title="Aucune inspection sur cette période. Lance une analyse depuis Live Monitoring." /></div>
          ) : (
            <>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-ink-dim text-xs uppercase bg-surface-hover">
                    <th className="py-2.5 px-4 font-medium">Heure</th>
                    <th className="px-4 font-medium">Machine</th>
                    <th className="px-4 font-medium">Prédiction</th>
                    <th className="px-4 font-medium">Niveau d'usure</th>
                    <th className="px-4 font-medium">Confiance</th>
                    <th className="px-4 font-medium">Statut</th>
                    <th className="px-4 font-medium">Image</th>
                  </tr>
                </thead>
                <tbody>
                  {pageItems.map((p) => (
                    <tr key={p.id} className="border-t border-surface-border">
                      <td className="py-2.5 px-4 font-mono text-xs text-ink-mid">{new Date(p.created_at).toLocaleString("fr-FR")}</td>
                      <td className="px-4 text-ink-hi">#{p.machine_id}</td>
                      <td className="px-4"><ClassText predictedClass={p.predicted_class} /></td>
                      <td className="px-4 text-ink-mid">{wearLevelFromPrediction(p.predicted_class, p.confidence)}%</td>
                      <td className="px-4 text-ink-hi font-medium">{Math.round(p.confidence * 100)}%</td>
                      <td className="px-4"><StatusPill severity={severityFromClass(p.predicted_class)} /></td>
                      <td className="px-4">
                        {p.frame_path ? (
                          <img src={`${API_ORIGIN}${p.frame_path}`} alt="frame" className="w-10 h-10 object-cover rounded-md border border-surface-border" />
                        ) : (
                          <span className="text-ink-dim text-xs">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="flex items-center justify-between px-4 py-3 border-t border-surface-border text-xs text-ink-dim">
                <span>{predictions.length} résultat(s)</span>
                <div className="flex items-center gap-1.5">
                  <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
                    className="w-8 h-8 rounded-lg border border-surface-border text-ink-mid disabled:opacity-40 hover:bg-surface-hover">‹</button>
                  {Array.from({ length: totalPages }, (_, i) => i + 1).slice(0, 6).map((p) => (
                    <button key={p} onClick={() => setPage(p)}
                      className={`w-8 h-8 rounded-lg text-sm font-medium ${p === page ? "bg-brand-600 text-white" : "text-ink-mid hover:bg-surface-hover border border-surface-border"}`}>
                      {p}
                    </button>
                  ))}
                  <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                    className="w-8 h-8 rounded-lg border border-surface-border text-ink-mid disabled:opacity-40 hover:bg-surface-hover">›</button>
                </div>
              </div>
            </>
          )
        )}
      </div>
    </DashboardLayout>
  );
}
