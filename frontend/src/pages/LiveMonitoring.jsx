import { useEffect, useState, useCallback, useRef } from "react";
import { LuPlay, LuPause, LuCamera, LuMaximize, LuChevronDown } from "react-icons/lu";
import DashboardLayout from "../components/layout/DashboardLayout";
import { StatusPill, ClassText } from "../components/ui/StatusBadge";
import WearLevelBar from "../components/ui/WearLevelBar";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import EmptyState from "../components/ui/EmptyState";
import { listVideos, processVideo } from "../api/monitoring";
import { listMachines, listTools } from "../api/machines";
import { API_ORIGIN } from "../api/axiosClient";
import { severityFromClass, wearLevelFromPrediction } from "../components/ui/statusMeta";

const LOOP_MAX_FRAMES = 20;
const LOOP_FRAME_INTERVAL = 2;
const LOOP_PAUSE_MS = 8000; // pause entre deux passages d'analyse, pour ne pas saturer l'API

export default function LiveMonitoring() {
  const videoRef = useRef(null);
  const containerRef = useRef(null);
  const loopTimerRef = useRef(null);
  const stoppedRef = useRef(false);

  const [videos, setVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState("");
  const [sourceMenuOpen, setSourceMenuOpen] = useState(false);
  const [machine, setMachine] = useState(null);
  const [tool, setTool] = useState(null);

  const [initLoading, setInitLoading] = useState(true);
  const [initError, setInitError] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [processError, setProcessError] = useState(null);
  const [recentPredictions, setRecentPredictions] = useState([]);
  const [isPlaying, setIsPlaying] = useState(true);
  const [snapshotUrl, setSnapshotUrl] = useState(null);

  const latest = recentPredictions[0];

  // --- Chargement initial : machine/outil fixes + vidéos disponibles ---
  const loadInit = useCallback(async () => {
    setInitLoading(true);
    setInitError(null);
    try {
      const [videosRes, machines] = await Promise.all([listVideos(), listMachines()]);
      setVideos(videosRes.videos);
      const m = machines[0] || null;
      setMachine(m);
      if (m) {
        const tools = await listTools(m.id);
        setTool(tools[0] || null);
      }
      if (videosRes.videos.length > 0) setSelectedVideo(videosRes.videos[0]);
    } catch (err) {
      setInitError(err);
    } finally {
      setInitLoading(false);
    }
  }, []);

  useEffect(() => { loadInit(); }, [loadInit]);

  // --- Boucle d'analyse réelle : relance process-video périodiquement tant
  // que la page est ouverte, pour simuler une surveillance continue sur la
  // vidéo simulée (pas un vrai flux caméra, voir docs/WORKFLOW.md). ---
  const runAnalysisLoop = useCallback(async () => {
    if (!machine || !tool || !selectedVideo || stoppedRef.current) return;
    setProcessing(true);
    setProcessError(null);
    try {
      const result = await processVideo({
        video_filename: selectedVideo,
        machine_id: machine.id,
        tool_id: tool.id,
        frame_interval_seconds: LOOP_FRAME_INTERVAL,
        max_frames: LOOP_MAX_FRAMES,
      });
      setRecentPredictions([...result.predictions].reverse());
    } catch (err) {
      setProcessError(err);
    } finally {
      setProcessing(false);
      if (!stoppedRef.current) {
        loopTimerRef.current = setTimeout(runAnalysisLoop, LOOP_PAUSE_MS);
      }
    }
  }, [machine, tool, selectedVideo]);

  useEffect(() => {
    stoppedRef.current = false;
    if (machine && tool && selectedVideo) {
      runAnalysisLoop();
    }
    return () => {
      stoppedRef.current = true;
      clearTimeout(loopTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [machine, tool, selectedVideo]);

  function handleChangeSource(filename) {
    setSelectedVideo(filename);
    setSourceMenuOpen(false);
    setRecentPredictions([]);
    if (videoRef.current) videoRef.current.load();
  }

  function togglePlay() {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) { v.play(); setIsPlaying(true); } else { v.pause(); setIsPlaying(false); }
  }

  function takeSnapshot() {
    const v = videoRef.current;
    if (!v) return;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    canvas.getContext("2d").drawImage(v, 0, 0);
    setSnapshotUrl(canvas.toDataURL("image/jpeg"));
  }

  function toggleFullscreen() {
    if (containerRef.current) containerRef.current.requestFullscreen?.();
  }

  const latestSeverity = latest ? severityFromClass(latest.predicted_class) : null;
  const SEVERITY_COLOR = { critical: "#E11D48", warning: "#D97706", normal: "#16A34A" };

  if (initLoading) return <DashboardLayout title="Live Monitoring"><LoadingState label="Connexion au backend…" /></DashboardLayout>;
  if (initError) return <DashboardLayout title="Live Monitoring"><ErrorState error={initError} onRetry={loadInit} /></DashboardLayout>;

  return (
    <DashboardLayout
      title="Surveillance en direct"
      subtitle={machine?.name}
      topbarChildren={
        videos.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setSourceMenuOpen((v) => !v)}
              className="flex items-center gap-2 bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-sm text-ink-mid hover:bg-surface-hover"
            >
              Source : <span className="text-ink-hi font-medium">{selectedVideo}</span>
              <LuChevronDown size={14} />
            </button>
            {sourceMenuOpen && (
              <div className="absolute right-0 mt-2 w-64 bg-surface-card border border-surface-border rounded-lg shadow-panel py-1.5 text-sm z-20">
                {videos.map((v) => (
                  <button
                    key={v}
                    onClick={() => handleChangeSource(v)}
                    className={`w-full text-left px-3 py-2 hover:bg-surface-hover ${v === selectedVideo ? "text-brand-600 font-medium" : "text-ink-hi"}`}
                  >
                    {v}
                  </button>
                ))}
              </div>
            )}
          </div>
        )
      }
    >
      {videos.length === 0 ? (
        <EmptyState title="Aucune vidéo trouvée dans backend/videos/. Dépose un fichier .mp4 (simulation caméra) puis recharge la page." />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Video panel */}
          <div className="lg:col-span-2 bg-surface-card border border-surface-border rounded-card shadow-card overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
              <p className="text-sm font-semibold text-ink-hi">Surveillance en direct — {machine?.name}</p>
              <span className="flex items-center gap-1.5 bg-status-criticalBg text-status-critical text-xs font-semibold px-2.5 py-1 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-status-critical live-dot" /> EN DIRECT
              </span>
            </div>

            <div ref={containerRef} className="relative bg-black aspect-video">
              <video
                ref={videoRef}
                src={`${API_ORIGIN}/media/${encodeURIComponent(selectedVideo)}`}
                autoPlay muted loop playsInline
                className="w-full h-full object-contain"
              />
              {latest && latestSeverity && (
                <div
                  className="absolute inset-2 rounded-md pointer-events-none"
                  style={{ border: `3px solid ${SEVERITY_COLOR[latestSeverity]}` }}
                >
                  <span
                    className="absolute top-2 left-2 px-2 py-1 rounded text-xs font-bold text-white"
                    style={{ backgroundColor: SEVERITY_COLOR[latestSeverity] }}
                  >
                    {latest.predicted_class.toUpperCase()} {Math.round(latest.confidence * 100)}%
                  </span>
                </div>
              )}
            </div>

            <div className="flex items-center gap-3 px-4 py-3 border-t border-surface-border">
              <button onClick={togglePlay} className="w-8 h-8 rounded-lg bg-surface-hover flex items-center justify-center text-ink-mid hover:text-ink-hi">
                {isPlaying ? <LuPause size={15} /> : <LuPlay size={15} />}
              </button>
              <button onClick={takeSnapshot} className="w-8 h-8 rounded-lg bg-surface-hover flex items-center justify-center text-ink-mid hover:text-ink-hi" title="Capture">
                <LuCamera size={15} />
              </button>
              <button onClick={toggleFullscreen} className="w-8 h-8 rounded-lg bg-surface-hover flex items-center justify-center text-ink-mid hover:text-ink-hi" title="Plein écran">
                <LuMaximize size={15} />
              </button>
              {processing && <span className="text-xs text-ink-dim ml-2">Analyse en cours…</span>}
              {processError && <span className="text-xs text-status-critical ml-2">Erreur d'analyse — voir ci-dessous</span>}
            </div>
          </div>

          {/* Résultat actuel */}
          <div className="bg-surface-card border border-surface-border rounded-card p-5 shadow-card">
            <p className="text-sm font-semibold text-ink-hi mb-3">Résultat actuel</p>
            {!latest ? (
              <EmptyState title="Premier passage d'analyse en cours…" />
            ) : (
              <div className="space-y-3">
                <StatusPill severity={severityFromClass(latest.predicted_class)} />
                <ClassText predictedClass={latest.predicted_class} />
                <WearLevelBar predictedClass={latest.predicted_class} wearLevel={wearLevelFromPrediction(latest.predicted_class, latest.confidence)} />
                <div className="grid grid-cols-2 gap-y-2 text-sm pt-1">
                  <span className="text-ink-mid">Confiance</span>
                  <span className="text-right font-semibold text-ink-hi">{Math.round(latest.confidence * 100)}%</span>
                  <span className="text-ink-mid">Heure</span>
                  <span className="text-right font-mono text-ink-hi">{new Date().toLocaleTimeString("fr-FR")}</span>
                  <span className="text-ink-mid">Machine</span>
                  <span className="text-right text-ink-hi">{machine?.name}</span>
                </div>
              </div>
            )}

            <div className="mt-5 pt-4 border-t border-surface-border text-sm">
              <p className="text-xs font-semibold text-ink-dim uppercase tracking-wide mb-2">Informations machine</p>
              <div className="grid grid-cols-2 gap-y-1.5 text-xs">
                <span className="text-ink-mid">ID Machine</span><span className="text-right text-ink-hi">{machine?.camera_id}</span>
                <span className="text-ink-mid">Source</span><span className="text-right text-ink-hi truncate">{selectedVideo}</span>
                <span className="text-ink-mid">Modèle IA</span><span className="text-right text-ink-hi">EfficientNetV2B0</span>
                <span className="text-ink-mid">Outil suivi</span><span className="text-right text-ink-hi">{tool?.tool_identifier}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {processError && <div className="mt-5"><ErrorState error={processError} /></div>}

      {snapshotUrl && (
        <div className="mt-5 bg-surface-card border border-surface-border rounded-card p-4 shadow-card">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-semibold text-ink-hi">Capture</p>
            <button onClick={() => setSnapshotUrl(null)} className="text-xs text-ink-dim hover:text-ink-hi">Fermer</button>
          </div>
          <img src={snapshotUrl} alt="Capture" className="rounded-lg max-h-64" />
        </div>
      )}

      {/* Historique récent temps réel */}
      <div className="mt-5 bg-surface-card border border-surface-border rounded-card shadow-card overflow-hidden">
        <p className="text-sm font-semibold text-ink-hi px-4 py-3 border-b border-surface-border">Historique récent (temps réel)</p>
        {recentPredictions.length === 0 ? (
          <div className="p-6"><EmptyState title="En attente du premier résultat d'analyse…" /></div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-dim text-xs uppercase bg-surface-hover">
                <th className="py-2.5 px-4 font-medium">Frame</th>
                <th className="px-4 font-medium">Prédiction</th>
                <th className="px-4 font-medium">Confiance</th>
                <th className="px-4 font-medium">Niveau d'usure</th>
                <th className="px-4 font-medium">Statut</th>
              </tr>
            </thead>
            <tbody>
              {recentPredictions.slice(0, 8).map((p) => (
                <tr key={p.prediction_id} className="border-t border-surface-border">
                  <td className="py-2 px-4 font-mono text-xs text-ink-mid">#{p.frame_index} · {p.timestamp_seconds}s</td>
                  <td className="px-4"><ClassText predictedClass={p.predicted_class} /></td>
                  <td className="px-4 text-ink-hi font-medium">{Math.round(p.confidence * 100)}%</td>
                  <td className="px-4 text-ink-mid">{wearLevelFromPrediction(p.predicted_class, p.confidence)}%</td>
                  <td className="px-4"><StatusPill predictedClass={p.predicted_class} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </DashboardLayout>
  );
}
