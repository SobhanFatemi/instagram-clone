import { api } from "./client";

export async function getMe() {
  const { data } = await api.get("/auth/me/");
  return data;
}

export async function updateMe(payload) {
  const { data } = await api.patch("/auth/me/", payload);
  return data;
}

export async function deleteMe() {
  await api.delete("/auth/me/");
}

export async function requestContactOtp(payload) {
  const { data } = await api.post("/auth/contact/request/", payload);
  return data;
}

export async function verifyContactOtp(payload) {
  const { data } = await api.post("/auth/contact/verify/", payload);
  return data;
}
