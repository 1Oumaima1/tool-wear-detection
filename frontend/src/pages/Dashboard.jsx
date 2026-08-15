import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { LuActivity, LuClock, LuScanLine, LuTriangleAlert, LuMail, LuPlay } from "react-icons/lu";
import DashboardLayout from "../components/layout/DashboardLayout";
import StatCard from "../components/ui/StatCard";
import { StatusPill, ClassText } from "../components/ui/StatusBadge";
import WearLevelBar from "../components/ui/WearLevelBar";
import WearTrendChart from "../components/ui/WearTrendChart";
import ClassDistributionDonut from "../components/ui/ClassDistributionDonut";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import EmptyState from "../components/ui/EmptyState";
import { listMachines } from "../api/machines";
import { listPredictions } from "../api/predictions";
import { listAlerts } from "../api/alerts";
import { API_ORIGIN } from "../api/axiosClient";
import { wearLevelFromPrediction } from "../components/ui/statusMeta";

function startOfToday() {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
}
function isToday(dateStr) {
  return new Date(dateStr) >= startOfToday();
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [machine, setMachine] = useState(null);
  const [todaysPredictions, setTodaysPredictions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const machines = await listMachines();
      const m = machines[0] || null;
      setMachine(m);

      const [predictions, alertsList] = await Promise.all([
        listPredictions({
          machine_id: m?.id,
          date_from: startOfToday().toISOString(),
          limit: 500,
        }),
        listAlerts(m?.id ? { machine_id: m.id } : {}),
      ]);
      setTodaysPredictions(predictions);
      setAlerts(alertsList);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [load]);

  if (loading) return <DashboardLayout title="Dashboard"><LoadingState label="Chargement du système…" /></DashboardLayout>;
  if (error) return <DashboardLayout title="Dashboard"><ErrorState error={error} onRetry={load} /></DashboardLayout>;

  const last = todaysPredictions[0]; // API renvoie déjà par created_at desc
  const todaysAlerts = alerts.filter((a) => isToday(a.created_at));
  const unresolvedCritical = alerts.filter((a) => !a.resolved).length;
  const emailsToday = alerts.filter((a) => isToday(a.created_at) && a.email_sent).length;

  const distribution = { sharp: 0, used: 0, dulled: 0 };
  todaysPredictions.forEach((p) => { if (distribution[p.predicted_class] !== undefined) distribution[p.predicted_class]++; });

  const trendData = [...todaysPredictions]
    .slice(0, 30)
    .reverse()
    .map((p) => ({
      time: new Date(p.created_at).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }),
      wearLevel: wearLevelFromPrediction(p.predicted_class, p.confidence),
    }));

  return (
    <DashboardLayout title="Vue d'ensemble du système" subtitle={`Surveillance de l'usure d'outils — ${machine?.name || "—"}`}>
      <div className="space-y-5">
        {/* KPI cards */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard icon={LuActivity} label="Statut système" value="ACTIF" accent="text-status-normal" iconBg="bg-status-normalBg" iconColor="text-status-normal" sub="Tout fonctionne" />
          <StatCard icon={LuClock} label="Dernière détection" value={last ? new Date(last.created_at).toLocaleTimeString("fr-FR") : "—"} sub="Aujourd'hui" />
          <StatCard icon={LuScanLine} label="Inspections aujourd'hui" value={todaysPredictions.length} sub={`sur ${machine?.name || "—"}`} />
          <StatCard
            icon={LuTriangleAlert} label="Alertes critiques" value={unresolvedCritical}
            accent={unresolvedCritical > 0 ? "text-status-critical" : "text-ink-hi"}
            iconBg="bg-status-criticalBg" iconColor="text-status-critical" sub="Non résolues"
          />
          <StatCard icon={LuMail} label="Emails envoyés" value={emailsToday} sub="Aujourd'hui" iconBg="bg-status-infoBg" iconColor="text-status-info" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* État actuel */}
          <div className="bg-surface-card border border-surface-border rounded-card p-5 shadow-card">
            <p className="text-sm font-semibold text-ink-hi mb-3">État actuel (Dernière détection)</p>
            {!last ? (
              <EmptyState title="Aucune inspection aujourd'hui. Lance une analyse depuis Live Monitoring." />
            ) : (
              <div className="space-y-3">
                <StatusPill predictedClass={last.predicted_class} />
                <WearLevelBar predictedClass={last.predicted_class} wearLevel={wearLevelFromPrediction(last.predicted_class, last.confidence)} />
                <div className="grid grid-cols-2 gap-y-2 text-sm pt-1">
                  <span className="text-ink-mid">Prédiction</span>
                  <span className="text-right"><ClassText predictedClass={last.predicted_class} /></span>
                  <span className="text-ink-mid">Confiance</span>
                  <span className="text-right font-semibold text-ink-hi">{Math.round(last.confidence * 100)}%</span>
                  <span className="text-ink-mid">Heure</span>
                  <span className="text-right font-mono text-ink-hi">{new Date(last.created_at).toLocaleTimeString("fr-FR")}</span>
                  <span className="text-ink-mid">Machine</span>
                  <span className="text-right text-ink-hi">{machine?.name}</span>
                </div>
              </div>
            )}
          </div>

          {/* Évolution */}
          <div className="lg:col-span-2 bg-surface-card border border-surface-border rounded-card p-5 shadow-card">
            <p className="text-sm font-semibold text-ink-hi mb-3">Évolution du niveau d'usure (Aujourd'hui)</p>
            {trendData.length === 0 ? (
              <EmptyState title="Pas encore de données aujourd'hui." />
            ) : (
              <WearTrendChart data={trendData} />
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Aperçu + voir en direct */}
          <div className="bg-surface-card border border-surface-border rounded-card p-5 shadow-card">
            <p className="text-sm font-semibold text-ink-hi mb-3">Aperçu dernière détection</p>
            <div
              className="rounded-lg overflow-hidden bg-ink-hi/5 aspect-video mb-3 flex items-center justify-center cursor-pointer"
              onClick={() => navigate("/live-monitoring")}
            >
              {last?.frame_path ? (
                <img src={`${API_ORIGIN}${last.frame_path}`} alt="Dernière frame" className="w-full h-full object-cover" />
              ) : (
                <LuScanLine className="text-ink-dim" size={28} />
              )}
            </div>
            <button
              onClick={() => navigate("/live-monitoring")}
              className="w-full flex items-center justify-center gap-2 bg-brand-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-brand-700"
            >
              <LuPlay size={14} /> Voir en direct
            </button>
          </div>

          {/* Donut répartition */}
          <div className="bg-surface-card border border-surface-border rounded-card p-5 shadow-card">
            <p className="text-sm font-semibold text-ink-hi mb-3">Répartition des prédictions (Aujourd'hui)</p>
            {todaysPredictions.length === 0 ? (
              <EmptyState title="Aucune prédiction aujourd'hui." />
            ) : (
              <ClassDistributionDonut distribution={distribution} />
            )}
          </div>

          {/* Dernières alertes */}
          <div className="bg-surface-card border border-surface-border rounded-card p-5 shadow-card">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold text-ink-hi">Dernières alertes</p>
              <button onClick={() => navigate("/alerts")} className="text-xs text-brand-600 font-medium hover:underline">
                Voir toutes les alertes →
              </button>
            </div>
            {alerts.length === 0 ? (
              <EmptyState title="Aucune alerte." />
            ) : (
              <div className="space-y-2">
                {alerts.slice(0, 4).map((a) => (
                  <div key={a.id} className="flex items-center justify-between text-sm border-b border-surface-border last:border-0 pb-2 last:pb-0">
                    <div>
                      <p className="font-mono text-xs text-ink-dim">{new Date(a.created_at).toLocaleTimeString("fr-FR")}</p>
                      <p className="text-ink-hi text-xs">{machine?.name}</p>
                    </div>
                    <StatusPill severity={a.severity} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
