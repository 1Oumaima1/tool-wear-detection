import { createContext, useContext, useState, useCallback } from "react";
import { login as loginApi } from "../api/auth";
import { decodeJwtPayload } from "../utils/jwt";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("agatronic_token"));
  const [username, setUsername] = useState(() => localStorage.getItem("agatronic_username"));
  const [role, setRole] = useState(() => localStorage.getItem("agatronic_user_role"));

  const [sessionStart, setSessionStart] = useState(() => {
    const stored = localStorage.getItem("agatronic_session_start");
    return stored ? Number(stored) : null;
  });

  const login = useCallback(async (user, password) => {
    const { access_token } = await loginApi(user, password);
    const payload = decodeJwtPayload(access_token) || {};
    const now = Date.now();

    localStorage.setItem("agatronic_token", access_token);
    localStorage.setItem("agatronic_username", payload.sub || user);
    localStorage.setItem("agatronic_user_role", payload.role || "");
    localStorage.setItem("agatronic_session_start", String(now));

    setToken(access_token);
    setUsername(payload.sub || user);
    setRole(payload.role || "");
    setSessionStart(now);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("agatronic_token");
    localStorage.removeItem("agatronic_username");
    localStorage.removeItem("agatronic_user_role");
    localStorage.removeItem("agatronic_session_start");
    setToken(null);
    setUsername(null);
    setRole(null);
    setSessionStart(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ token, username, role, sessionStart, isAuthenticated: !!token, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

