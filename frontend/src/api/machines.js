import apiClient from "./axiosClient";

export const listMachines = () => apiClient.get("/machines/").then((r) => r.data);

export const listTools = (machineId) =>
  apiClient.get(`/machines/${machineId}/tools`).then((r) => r.data);
