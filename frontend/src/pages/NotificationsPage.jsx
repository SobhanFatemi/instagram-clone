import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  clearNotifications,
  deleteNotification,
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../api/notifications";
import Avatar from "../components/Avatar";
import Spinner from "../components/Spinner";
import { timeAgo } from "../lib/time";

const POLL_INTERVAL = 15000;

function targetPath(notification) {
  const target = notification.target;
  if (notification.notification_type === "follow") {
    return notification.actor ? `/u/${notification.actor.username}` : null;
  }
  if (notification.notification_type === "message") {
    return "/messages";
  }
  if (target) {
    if (target.post_id) return `/p/${target.post_id}`;
    if (target.model === "post") return `/p/${target.id}`;
  }
  return notification.actor ? `/u/${notification.actor.username}` : null;
}

export default function NotificationsPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [next, setNext] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const pagesLoadedRef = useRef(1);

  const loadFirstPage = useCallback(async () => {
    const data = await getNotifications(1);
    setItems(data.results);
    setNext(data.next);
    setPage(1);
    pagesLoadedRef.current = 1;
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        await loadFirstPage();
      } catch {
        /* ignore */
      }
      if (active) setLoading(false);
    })();

    const timer = setInterval(() => {
      if (pagesLoadedRef.current === 1) {
        loadFirstPage().catch(() => {});
      }
    }, POLL_INTERVAL);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [loadFirstPage]);

  async function loadMore() {
    if (!next) return;
    try {
      const data = await getNotifications(page + 1);
      setItems((current) => [...current, ...data.results]);
      setNext(data.next);
      setPage((p) => p + 1);
      pagesLoadedRef.current += 1;
    } catch {
      /* ignore */
    }
  }

  async function open(notification) {
    if (!notification.is_read) {
      setItems((current) =>
        current.map((n) =>
          n.id === notification.id ? { ...n, is_read: true } : n
        )
      );
      markNotificationRead(notification.id).catch(() => {});
    }
    const path = targetPath(notification);
    if (path) navigate(path);
  }

  async function remove(event, notificationId) {
    event.stopPropagation();
    setItems((current) => current.filter((n) => n.id !== notificationId));
    try {
      await deleteNotification(notificationId);
    } catch {
      /* ignore */
    }
  }

  async function markAll() {
    setItems((current) => current.map((n) => ({ ...n, is_read: true })));
    try {
      await markAllNotificationsRead();
    } catch {
      loadFirstPage();
    }
  }

  async function clearAll() {
    if (!window.confirm("Clear all notifications?")) return;
    setItems([]);
    setNext(null);
    try {
      await clearNotifications();
    } catch {
      loadFirstPage();
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Notifications</h1>
        {items.length > 0 && (
          <div className="flex gap-2 text-sm">
            <button
              type="button"
              onClick={markAll}
              className="rounded-lg px-2.5 py-1.5 font-medium text-neutral-600 transition hover:bg-neutral-100"
            >
              Mark all read
            </button>
            <button
              type="button"
              onClick={clearAll}
              className="rounded-lg px-2.5 py-1.5 font-medium text-red-600 transition hover:bg-red-50"
            >
              Clear all
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <Spinner />
      ) : items.length === 0 ? (
        <p className="py-16 text-center text-sm text-neutral-400">
          No notifications yet.
        </p>
      ) : (
        <ul className="divide-y divide-neutral-100 overflow-hidden rounded-xl border border-neutral-200 bg-white">
          {items.map((notification) => (
            <li
              key={notification.id}
              onClick={() => open(notification)}
              className={`group flex cursor-pointer items-center gap-3 px-4 py-3 transition hover:bg-neutral-50 ${
                notification.is_read ? "" : "bg-sky-50/60"
              }`}
            >
              <Avatar
                src={notification.actor?.avatar}
                name={notification.actor?.username || "?"}
                size={44}
              />
              <div className="min-w-0 flex-1">
                <p className="text-sm text-neutral-800">
                  {notification.message}
                </p>
                <p className="text-xs text-neutral-400">
                  {timeAgo(notification.created_at)}
                </p>
              </div>
              {!notification.is_read && (
                <span className="h-2 w-2 shrink-0 rounded-full bg-sky-500" />
              )}
              <button
                type="button"
                onClick={(e) => remove(e, notification.id)}
                className="hidden shrink-0 rounded-full p-1.5 text-neutral-400 transition hover:bg-neutral-200 hover:text-neutral-700 group-hover:block"
                aria-label="Delete notification"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                >
                  <path d="M6 6l12 12M18 6 6 18" />
                </svg>
              </button>
            </li>
          ))}
        </ul>
      )}

      {next && (
        <button
          type="button"
          onClick={loadMore}
          className="mx-auto block rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium text-neutral-700 transition hover:bg-neutral-100"
        >
          Load more
        </button>
      )}
    </div>
  );
}
