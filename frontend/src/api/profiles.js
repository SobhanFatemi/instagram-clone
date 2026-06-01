import { api } from "./client";

export async function getMyProfile() {
  const { data } = await api.get("/profiles/me/");
  return data;
}

export async function getProfile(username) {
  const { data } = await api.get(`/profiles/${username}/`);
  return data;
}

export async function updateMyProfile(payload) {
  const { data } = await api.patch("/profiles/me/", payload);
  return data;
}
