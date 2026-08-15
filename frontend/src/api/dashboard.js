import apiClient from "./axiosClient";

export const getDashboardSummary = () =>
  apiClient.get("/dashboard/summary").then((r) => r.data);
