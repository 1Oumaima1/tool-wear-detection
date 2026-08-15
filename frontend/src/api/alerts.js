import apiClient from "./axiosClient";

export const listAlerts = (params = {}) =>
  apiClient.get("/alerts/", { params }).then((r) => r.data);

export const resolveAlert = (id) =>
  apiClient.patch(`/alerts/${id}/resolve`).then((r) => r.data);
