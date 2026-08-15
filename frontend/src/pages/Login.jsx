import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { LuShieldCheck } from "react-icons/lu";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Connexion au backend impossible. Vérifie que l'API tourne bien (uvicorn app.main:app)."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface-page flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <span className="w-12 h-12 rounded-xl bg-brand-600 flex items-center justify-center mb-3">
            <LuShieldCheck className="text-white" size={26} />
          </span>
          <p className="font-semibold text-2xl text-ink-hi">ToolVision</p>
          <p className="text-ink-dim text-sm mt-1">Industrial Monitoring</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-surface-card border border-surface-border rounded-card p-6 shadow-panel space-y-4"
        >
          <div>
            <label className="text-xs text-ink-mid font-medium">Email</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              className="mt-1 w-full bg-white border border-surface-border rounded-lg px-3 py-2 text-sm text-ink-hi focus:border-brand-500 outline-none"
            />
          </div>
          <div>
            <label className="text-xs text-ink-mid font-medium">Mot de passe</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 w-full bg-white border border-surface-border rounded-lg px-3 py-2 text-sm text-ink-hi focus:border-brand-500 outline-none"
            />
          </div>

          {error && (
            <p className="text-status-critical text-xs bg-status-criticalBg border border-status-critical/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 text-white font-medium rounded-lg py-2.5 text-sm hover:bg-brand-700 transition disabled:opacity-50"
          >
            {loading ? "Connexion…" : "Se connecter"}
          </button>
        </form>
      </div>
    </div>
  );
}
