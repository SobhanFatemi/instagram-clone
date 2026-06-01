import { api } from "./client";

export async function getExplore(page = 1) {
  const { data } = await api.get("/feed/explore/", { params: { page } });
  return data;
}

export async function searchUsers(q) {
  const { data } = await api.get("/feed/search/users/", { params: { q } });
  return data;
}

export async function searchPosts(q) {
  const { data } = await api.get("/feed/search/posts/", { params: { q } });
  return data;
}

export async function searchHashtags(q) {
  const { data } = await api.get("/feed/search/hashtags/", { params: { q } });
  return data;
}
