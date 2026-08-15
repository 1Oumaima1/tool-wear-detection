import { useEffect, useState, useCallback, useMemo } from "react";
import { LuCircleCheck, LuMailCheck, LuMailX } from "react-icons/lu";
import DashboardLayout from "../components/layout/DashboardLayout";
import { StatusPill, ClassText } from "../components/ui/StatusBadge";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import EmptyState from "../components/ui/EmptyState";
import { listAlerts, resolveAlert } from "../api/alerts";
import { API_ORIGIN } from "../api/axiosClient";
import { wearLevelFromPrediction } from "../components/ui/statusMeta";

const PAGE_SIZE = 8;

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [tab, setTab] = useState("all"); // all | critical | warning
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const [bulkBusy, setBulkBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setAlerts(await listAlerts({}));
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const counts = useMemo(() => ({
    all: alerts.length,
    critical: alerts.filter((a) => a.severity === "critical").length,
    warning: alerts.filter((a) => a.severity === "warning").length,
  }), [alerts]);

  const filtered = useMemo(() => {
    if (tab === "all") return alerts;
    return alerts.filter((a) => a.severity === tab);
  }, [alerts, tab]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageItems = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  async function handleResolve(id) {
    setBusyId(id);
    try {
      await resolveAlert(id);
      await load();
    } catch (err) {
      setError(err);
    } finally {
      setBusyId(null);
    }
  }

  async function handleResolveAllVisible() {
    const toResolve = pageItems.filter((a) => !a.resolved);
    if (toResolve.length === 0) return;
    setBulkBusy(true);
    try {
      await Promise.all(toResolve.map((a) => resolveAlert(a.id)));
      await load();
    } catch (err) {
      setError(err);
    } finally {
      setBulkBusy(false);
    }
  }

  return (
    <DashboardLayout
      title="Alertes"
      subtitle="Liste des alertes critiques et warnings"
      topbarChildren={
        <button
          onClick={handleResolveAllVisible}
          disabled={bulkBusy}
          className="flex items-center gap-2 bg-brand-600 text-white rounded-lg px-3.5 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
        >
          <LuCircleCheck size={15} /> {bulkBusy ? "…" : "Marquer tout comme résolu"}
        </button>
      }
    >
      <div className="bg-surface-card border border-surface-border rounded-card shadow-card overflow-hidden">
        <div className="flex items-center gap-1 p-3 border-b border-surface-border">
          {[
            { key: "all", label: `Toutes (${counts.all})` },
            { key: "critical", label: `Critiques (${counts.critical})` },
            { key: "warning", label: `Warnings (${counts.warning})` },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => { setTab(t.key); setPage(1); }}
              className={`px-3.5 py-1.5 rounded-lg text-sm font-medium ${
                tab === t.key ? "bg-brand-50 text-brand-700" : "text-ink-mid hover:bg-surface-hover"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {loading && <LoadingState label="Chargement des alertes…" />}
        {error && <div className="p-4"><ErrorState error={error} onRetry={load} /></div>}

        {!loading && !error && (
          filtered.length === 0 ? (
            <div className="p-6"><EmptyState title="Aucune alerte pour ce filtre." /></div>
          ) : (
            <>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-ink-dim text-xs uppercase bg-surface-hover">
                    <th className="py-2.5 px-4 font-medium">Heure</th>
                    <th className="px-4 font-medium">Machine</th>
                    <th className="px-4 font-medium">Type</th>
                    <th className="px-4 font-medium">Niveau d'usure</th>
                    <th className="px-4 font-medium">Confiance</th>
                    <th className="px-4 font-medium">Image</th>
                    <th className="px-4 font-medium">Statut</th>
                    <th className="px-4 font-medium">Email</th>
                    <th className="px-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {pageItems.map((a) => (
                    <tr key={a.id} className="border-t border-surface-border">
                      <td className="py-2.5 px-4 font-mono text-xs text-ink-mid">{new Date(a.created_at).toLocaleString("fr-FR")}</td>
                      <td className="px-4 text-ink-hi">#{a.machine_id}</td>
                      <td className="px-4"><ClassText predictedClass="dulled" /></td>
                      <td className="px-4 text-ink-mid">{wearLevelFromPrediction("dulled", a.confidence || 0)}%</td>
                      <td className="px-4 text-ink-hi font-medium">{a.confidence ? `${Math.round(a.confidence * 100)}%` : "—"}</td>
                      <td className="px-4">
                        {a.frame_path ? (
                          <img src={`${API_ORIGIN}${a.frame_path}`} alt="frame" className="w-10 h-10 object-cover rounded-md border border-surface-border" />
                        ) : (
                          <span className="text-ink-dim text-xs">—</span>
                        )}
                      </td>
                      <td className="px-4"><StatusPill severity={a.resolved ? "normal" : a.severity} /></td>
                      <td className="px-4">
                        {a.email_sent ? (
                          <span className="flex items-center gap-1 text-status-normal text-xs"><LuMailCheck size={13} /> Envoyé</span>
                        ) : (
                          <span className="flex items-center gap-1 text-status-critical text-xs"><LuMailX size={13} /> Échec</span>
                        )}
                      </td>
                      <td className="px-4 text-right">
                        {!a.resolved && (
                          <button
                            onClick={() => handleResolve(a.id)}
                            disabled={busyId === a.id}
                            className="text-xs font-medium text-brand-600 hover:underline disabled:opacity-50"
                          >
                            {busyId === a.id ? "…" : "Résoudre"}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="flex items-center justify-center gap-1.5 py-4">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="w-8 h-8 rounded-lg border border-surface-border text-ink-mid disabled:opacity-40 hover:bg-surface-hover"
                >‹</button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).slice(0, 6).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`w-8 h-8 rounded-lg text-sm font-medium ${
                      p === page ? "bg-brand-600 text-white" : "text-ink-mid hover:bg-surface-hover border border-surface-border"
                    }`}
                  >{p}</button>
                ))}
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="w-8 h-8 rounded-lg border border-surface-border text-ink-mid disabled:opacity-40 hover:bg-surface-hover"
                >›</button>
              </div>
            </>
          )
        )}
      </div>
    </DashboardLayout>
  );
}
