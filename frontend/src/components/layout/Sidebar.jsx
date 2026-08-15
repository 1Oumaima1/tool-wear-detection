import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { LuLayoutDashboard, LuVideo, LuBellRing, LuHistory } from "react-icons/lu";
import { getHealth } from "../../api/system";
import { listMachines } from "../../api/machines";
import { useAuth } from "../../context/AuthContext";
import { formatElapsed } from "../../utils/formatters";
import agatronicLogo from "../../assets/agatronic-logo.png";
const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LuLayoutDashboard },
  { to: "/live-monitoring", label: "Live Monitoring", icon: LuVideo },
  { to: "/alerts", label: "Alerts", icon: LuBellRing },
  { to: "/history", label: "History", icon: LuHistory },
];

export default function Sidebar() {
  const { sessionStart } = useAuth();
  const [modelLoaded, setModelLoaded] = useState(null);
  const [machine, setMachine] = useState(null);
  const [elapsed, setElapsed] = useState(formatElapsed(sessionStart));

  useEffect(() => {
    getHealth().then((h) => setModelLoaded(h.model_loaded)).catch(() => setModelLoaded(false));
    listMachines().then((list) => setMachine(list[0] || null)).catch(() => setMachine(null));
  }, []);

  useEffect(() => {
    const t = setInterval(() => setElapsed(formatElapsed(sessionStart)), 1000);
    return () => clearInterval(t);
  }, [sessionStart]);

  const systemOnline = modelLoaded === true;

  return (
    <aside className="w-60 shrink-0 bg-surface-sidebar border-r border-surface-border flex flex-col h-screen sticky top-0">
    

          <div className="px-5 py-5 flex items-center gap-3 border-b border-surface-border">
              <img
                src={agatronicLogo}
                alt="Agatronic"
                className="w-11 h-11 object-contain"
              />

              <div>
                <p className="font-semibold text-ink-hi text-sm leading-none">
                  ToolVision
                </p>
                <p className="text-ink-dim text-[10px] mt-0.5">
                  Industrial Monitoring
                </p>
              </div>
            </div>

      <nav className="flex-1 overflow-y-auto py-3 px-3 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-brand-600 text-white"
                  : "text-ink-mid hover:bg-surface-hover hover:text-ink-hi"
              }`
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="m-3 p-4 rounded-card bg-surface-hover border border-surface-border text-sm">
        <p className="text-[11px] font-semibold text-ink-dim uppercase tracking-wide mb-2">Système</p>
        <div className="flex items-center gap-2 mb-3">
          <span className={`w-2 h-2 rounded-full ${systemOnline ? "bg-status-normal live-dot" : "bg-status-critical"}`} />
          <span className={`text-sm font-semibold ${systemOnline ? "text-status-normal" : "text-status-critical"}`}>
            {modelLoaded === null ? "Vérification…" : systemOnline ? "ACTIF" : "MODÈLE HORS LIGNE"}
          </span>
        </div>
        {machine && (
          <>
            <p className="text-ink-hi font-medium">{machine.name}</p>
            <p className="text-ink-dim text-xs">Simulation vidéo</p>
          </>
        )}
        <p className="text-ink-dim text-xs mt-3">
          En ligne depuis <span className="font-mono text-ink-mid">{elapsed}</span>
        </p>
      </div>
    </aside>
  );
}
