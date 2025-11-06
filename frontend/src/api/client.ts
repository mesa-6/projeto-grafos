import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:3000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10_000,
});

export default api;
