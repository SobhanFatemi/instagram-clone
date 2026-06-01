import { api } from "./client";

export async function followUser(userId) {
  const { data } = await api.post(`/social/follow/${userId}/`);
  return data;
}

export async function unfollowUser(userId) {
  const { data } = await api.post(`/social/unfollow/${userId}/`);
  return data;
}

export async function getFollowers(userId) {
  const { data } = await api.get(`/social/followers/${userId}/`);
  return data;
}

export async function getFollowing(userId) {
  const { data } = await api.get(`/social/following/${userId}/`);
  return data;
}

export async function getMutualFollowers(userId) {
  const { data } = await api.get(`/social/mutual-followers/${userId}/`);
  return data;
}

export async function blockUser(userId) {
  const { data } = await api.post(`/social/block/${userId}/`);
  return data;
}

export async function unblockUser(userId) {
  const { data } = await api.post(`/social/unblock/${userId}/`);
  return data;
}

export async function getBlockedUsers() {
  const { data } = await api.get("/social/blocked-users/");
  return data;
}
