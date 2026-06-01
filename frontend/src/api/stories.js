import { api } from "./client";

export async function getStoryFeed() {
  const { data } = await api.get("/stories/");
  return data;
}

export async function getMyStories() {
  const { data } = await api.get("/stories/my/");
  return data;
}

export async function getStory(storyId) {
  const { data } = await api.get(`/stories/${storyId}/`);
  return data;
}

export async function createStory(formData) {
  const { data } = await api.post("/stories/", formData);
  return data;
}

export async function deleteStory(storyId) {
  await api.delete(`/stories/${storyId}/`);
}

export async function markStoryViewed(storyId) {
  const { data } = await api.post(`/stories/${storyId}/view/`);
  return data;
}

export async function getStoryViewers(storyId) {
  const { data } = await api.get(`/stories/${storyId}/viewers/`);
  return data;
}

export async function getStoryComments(storyId, page = 1) {
  const { data } = await api.get(`/stories/${storyId}/comments/`, {
    params: { page },
  });
  return data;
}

export async function createStoryComment(storyId, payload) {
  const { data } = await api.post(`/stories/${storyId}/comments/`, payload);
  return data;
}

export async function deleteStoryComment(commentId) {
  await api.delete(`/stories/comments/${commentId}/`);
}
