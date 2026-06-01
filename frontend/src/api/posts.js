import { api } from "./client";

export async function getFeed(page = 1) {
  const { data } = await api.get("/feed/", { params: { page } });
  return data;
}

export async function listPosts({ author, page = 1 } = {}) {
  const { data } = await api.get("/posts/posts/", { params: { author, page } });
  return data;
}

export async function getPost(postId) {
  const { data } = await api.get(`/posts/posts/${postId}/`);
  return data;
}

export async function createPost(formData) {
  const { data } = await api.post("/posts/posts/", formData);
  return data;
}

export async function updatePost(postId, formData) {
  const { data } = await api.patch(`/posts/posts/${postId}/`, formData);
  return data;
}

export async function deletePost(postId) {
  await api.delete(`/posts/posts/${postId}/`);
}

export async function likePost(postId) {
  const { data } = await api.post(`/posts/${postId}/like/`);
  return data;
}

export async function unlikePost(postId) {
  const { data } = await api.delete(`/posts/${postId}/like/`);
  return data;
}

export async function savePost(postId) {
  const { data } = await api.post(`/posts/${postId}/save/`);
  return data;
}

export async function unsavePost(postId) {
  const { data } = await api.delete(`/posts/${postId}/save/`);
  return data;
}

export async function getSavedPosts(page = 1) {
  const { data } = await api.get("/posts/saved/", { params: { page } });
  return data;
}

export async function getComments(postId, page = 1) {
  const { data } = await api.get(`/posts/${postId}/comments/`, {
    params: { page },
  });
  return data;
}

export async function createComment(postId, payload) {
  const { data } = await api.post(`/posts/${postId}/comments/`, payload);
  return data;
}

export async function deleteComment(commentId) {
  const { data } = await api.delete(`/posts/${commentId}/`);
  return data;
}
