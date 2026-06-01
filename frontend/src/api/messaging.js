import { api } from "./client";

export async function getConversations(options = {}) {
  const params = {};
  if (options.hidden) {
    params.hidden = "true";
  }
  const { data } = await api.get("/messaging/conversations/", { params });
  return data;
}

export async function getConversation(conversationId) {
  const { data } = await api.get(`/messaging/conversations/${conversationId}/`);
  return data;
}

export async function createDirectConversation(userId) {
  const { data } = await api.post("/messaging/conversations/direct/", {
    user_id: userId,
  });
  return data;
}

export async function createGroupConversation(formData) {
  const { data } = await api.post("/messaging/conversations/group/", formData);
  return data;
}

export async function getConversationMessages(conversationId) {
  const { data } = await api.get(
    `/messaging/conversations/${conversationId}/messages/`
  );
  return data;
}

export async function markConversationRead(conversationId, lastReadMessageId) {
  const payload = {};
  if (lastReadMessageId) {
    payload.last_read_message_id = lastReadMessageId;
  }
  const { data } = await api.post(
    `/messaging/conversations/${conversationId}/mark-read/`,
    payload
  );
  return data;
}

export async function hideConversation(conversationId) {
  const { data } = await api.post(
    `/messaging/conversations/${conversationId}/hide/`
  );
  return data;
}

export async function unhideConversation(conversationId) {
  const { data } = await api.post(
    `/messaging/conversations/${conversationId}/unhide/`
  );
  return data;
}

export async function sendMessage(formData) {
  const { data } = await api.post("/messaging/messages/", formData);
  return data;
}

export async function deleteMessageForMe(messageId) {
  const { data } = await api.post(
    `/messaging/messages/${messageId}/delete-for-me/`
  );
  return data;
}

export async function deleteMessageForEveryone(messageId) {
  const { data } = await api.post(
    `/messaging/messages/${messageId}/delete-for-everyone/`
  );
  return data;
}

export async function markMessageSeen(messageId) {
  const { data } = await api.post(`/messaging/messages/${messageId}/mark-seen/`);
  return data;
}
