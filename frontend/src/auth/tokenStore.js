const ACCESS_KEY = "ig_access";
const REFRESH_KEY = "ig_refresh";

export function getAccess() {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefresh() {
  return localStorage.getItem(REFRESH_KEY);
}

export function setAccess(token) {
  localStorage.setItem(ACCESS_KEY, token);
}

export function setRefresh(token) {
  localStorage.setItem(REFRESH_KEY, token);
}

export function setTokens({ access, refresh }) {
  if (access) setAccess(access);
  if (refresh) setRefresh(refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}
