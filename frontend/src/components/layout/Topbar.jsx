import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LuBell, LuChevronDown, LuLogOut, LuUser } from "react-icons/lu";
import { useAuth } from "../../context/AuthContext";
import { listAlerts } from "../../api/alerts";

export default function Topbar({ title, subtitle, children }) {
  const { username, role, logout } = useAuth();
  const navigate = useNavigate();
  const [unresolvedCount, setUnresolvedCount] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const loadCount = () => {
      listAlerts({ resolved: false })
        .then((list) => setUnresolvedCount(list.length))
        .catch(() => {});
    };
    loadCount();
    const t = setInterval(loadCount, 20000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    function onClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-10 bg-surface-page/95 backdrop-blur border-b border-surface-border">
      <div className="flex items-center justify-between px-6 py-4 gap-4">
        <div className="min-w-0">
          <h1 className="font-semibold text-xl text-ink-hi truncate">{title}</h1>
          {subtitle && <p className="text-ink-mid text-sm mt-0.5">{subtitle}</p>}
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {children}

          <button
            onClick={() => navigate("/alerts")}
            className="relative w-9 h-9 rounded-lg bg-surface-card border border-surface-border flex items-center justify-center hover:bg-surface-hover"
            title="Voir les alertes"
          >
            <LuBell size={16} className="text-ink-mid" />
            {unresolvedCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 bg-status-critical text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
                {unresolvedCount}
              </span>
            )}
          </button>

          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="flex items-center gap-2 pl-1.5 pr-2.5 py-1.5 rounded-lg bg-surface-card border border-surface-border hover:bg-surface-hover"
            >
              <span className="w-6 h-6 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center">
                <LuUser size={13} />
              </span>
              <span className="text-sm font-medium text-ink-hi capitalize">{username}</span>
              <LuChevronDown size={14} className="text-ink-dim" />
            </button>

            {menuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-surface-card border border-surface-border rounded-lg shadow-panel py-1.5 text-sm">
                <div className="px-3 py-2 border-b border-surface-border">
                  <p className="text-ink-hi font-medium capitalize">{username}</p>
                  <p className="text-ink-dim text-xs capitalize">{role}</p>
                </div>
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-2 px-3 py-2 text-status-critical hover:bg-surface-hover"
                >
                  <LuLogOut size={14} /> Déconnexion
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
