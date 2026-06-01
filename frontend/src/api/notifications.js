import { api } from "./client";

export async function getNotifications(page = 1) {
  const { data } = await api.get("/notifications/", {
    params: { page },
  });
  return data;
}

export async function getUnreadCount() {
  const { data } = await api.get("/notifications/unread-count/");
  return data;
}

export async function markNotificationRead(notificationId) {
  const { data } = await api.post(
    `/notifications/${notificationId}/mark-read/`
  );
  return data;
}

export async function markAllNotificationsRead() {
  const { data } = await api.post("/notifications/mark-all-read/");
  return data;
}

export async function deleteNotification(notificationId) {
  await api.delete(`/notifications/${notificationId}/delete/`);
}

export async function clearNotifications() {
  await api.delete("/notifications/clear/");
}
