import apiClient from "./axiosClient";

export const listVideos = () => apiClient.get("/monitoring/videos").then((r) => r.data);

export const processVideo = (payload) =>
  apiClient.post("/monitoring/process-video", payload).then((r) => r.data);
