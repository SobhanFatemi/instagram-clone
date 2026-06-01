import axios from "axios";

import {
  getAccess,
  getRefresh,
  setAccess,
  setRefresh,
  clearTokens,
} from "../auth/tokenStore";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
});

let onAuthFailure = null;

export function setOnAuthFailure(callback) {
  onAuthFailure = callback;
}

api.interceptors.request.use((config) => {
  const token = getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise = null;

async function refreshAccessToken() {
  const refresh = getRefresh();
  if (!refresh) {
    throw new Error("No refresh token available.");
  }

  const response = await axios.post(
    `${API_BASE_URL}/api/auth/token/refresh/`,
    { refresh }
  );

  const newAccess = response.data.access;
  const newRefresh = response.data.refresh;

  setAccess(newAccess);
  if (newRefresh) {
    setRefresh(newRefresh);
  }

  return newAccess;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    const isAuthError = error.response && error.response.status === 401;
    const isRefreshCall = originalRequest.url?.includes("/auth/token/refresh/");

    if (isAuthError && !originalRequest._retry && !isRefreshCall) {
      originalRequest._retry = true;

      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => {
            refreshPromise = null;
          });
        }
        const newAccess = await refreshPromise;
        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        return api(originalRequest);
      } catch (refreshError) {
        clearTokens();
        if (onAuthFailure) {
          onAuthFailure();
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
