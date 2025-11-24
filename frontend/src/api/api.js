// src/api/api.js
import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8000/api",
});

// GET wrapper
export async function apiGet(path) {
  const res = await api.get(path);
  return res.data;
}

// Search wrapper
export async function apiSearch(query) {
  const res = await api.get(`/search?q=${encodeURIComponent(query)}`);
  return res.data;
}

// POST wrapper
export async function apiPost(path, body) {
  const res = await api.post(path, body);
  return res.data;
}

// Get article by ID
export async function getArticle(id) {
  // Adjust endpoint if needed
  return api.get(`/articles/${id}`);
}

// Summarize article
export async function summarizeArticle(id, useAbstractive = true) {
  // Adjust endpoint and payload if needed
  return api.post(`/summarize/${id}`, { abstractive: useAbstractive });
}

