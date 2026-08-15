import axios from "axios";

// Toutes les requêtes passent par ce client -> jamais de données mockées,
// tout vient réellement du backend FastAPI des Phases 1 & 2.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

// Origine du backend (sans le suffixe /api/v1) — utilisée pour construire les
// URLs des images statiques servies par FastAPI (frames originales, Grad-CAM).
export const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, "");

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("agatronic_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("agatronic_token");
      localStorage.removeItem("agatronic_user_role");
      localStorage.removeItem("agatronic_username");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
