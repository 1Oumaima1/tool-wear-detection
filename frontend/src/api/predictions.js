import apiClient from "./axiosClient";

export const listPredictions = (params = {}) =>
  apiClient.get("/predictions/", { params }).then((r) => r.data);

export const getPrediction = (id) =>
  apiClient.get(`/predictions/${id}`).then((r) => r.data);
