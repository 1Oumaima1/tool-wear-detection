import axios from "axios";
import { API_ORIGIN } from "./axiosClient";

export const getHealth = () => axios.get(`${API_ORIGIN}/`).then((r) => r.data);
