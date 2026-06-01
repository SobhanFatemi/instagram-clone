import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  getConversations,
  hideConversation,
  unhideConversation,
} from "../api/messaging";
import { useAuth } from "../auth/AuthContext";
import Avatar from "../components/Avatar";
import NewMessageModal from "../components/NewMessageModal";
import Spinner from "../components/Spinner";
import {
  conversationAvatar,
  conversationTitle,
  messagePreview,
} from "../lib/conversation";
import { timeAgo } from "../lib/time";

const POLL_INTERVAL = 6000;

export default function MessagesPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [view, setView] = useState("inbox");

  const archived = view === "archived";

  const load = useCallback(async () => {
    try {
      setConversations(await getConversations({ hidden: archived }));
    } catch {
      /* keep current */
    }
  }, [archived]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    (async () => {
      await load();
      if (active) setLoading(false);
    })();
    const timer = setInterval(load, POLL_INTERVAL);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [load]);

  async function hide(event, conversationId) {
    event.stopPropagation();
    setConversations((current) =>
      current.filter((c) => c.id !== conversationId)
    );
    try {
      await hideConversation(conversationId);
    } catch {
      load();
    }
  }

  async function unhide(event, conversationId) {
    event.stopPropagation();
    setConversations((current) =>
      current.filter((c) => c.id !== conversationId)
    );
    try {
      await unhideConversation(conversationId);
      navigate(`/messages/${conversationId}`);
    } catch {
      load();
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Messages</h1>
        <button
          type="button"
          onClick={() => setShowNew(true)}
          className="rounded-lg bg-neutral-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-neutral-800"
        >
          New message
        </button>
      </div>

      <div className="flex gap-1.5">
        {["inbox", "archived"].map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setView(key)}
            className={`rounded-full px-3 py-1 text-sm font-medium transition ${
              view === key
                ? "bg-neutral-900 text-white"
                : "text-neutral-500 hover:bg-neutral-100"
            }`}
          >
            {key === "inbox" ? "Messages" : "Archived"}
          </button>
        ))}
      </div>

      {loading ? (
        <Spinner />
      ) : conversations.length === 0 ? (
        <p className="py-16 text-center text-sm text-neutral-400">
          {archived
            ? "No archived conversations."
            : "No conversations yet. Start a new message."}
        </p>
      ) : (
        <ul className="divide-y divide-neutral-100 overflow-hidden rounded-xl border border-neutral-200 bg-white">
          {conversations.map((conversation) => {
            const avatar = conversationAvatar(conversation, user?.id);
            const isGroup = conversation.conversation_type === "group";
            const unread = conversation.unread_count > 0;
            return (
              <li
                key={conversation.id}
                onClick={
                  archived
                    ? undefined
                    : () => navigate(`/messages/${conversation.id}`)
                }
                className={`group flex items-center gap-3 px-4 py-3 transition ${
                  archived
                    ? ""
                    : "cursor-pointer hover:bg-neutral-50"
                }`}
              >
                <Avatar src={avatar.src} name={avatar.name} size={52} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p
                      className={`truncate text-sm ${
                        unread
                          ? "font-semibold text-neutral-900"
                          : "font-medium text-neutral-800"
                      }`}
                    >
                      {conversationTitle(conversation, user?.id)}
                    </p>
                    <span className="shrink-0 text-xs text-neutral-400">
                      {timeAgo(
                        conversation.last_message_at ||
                          conversation.created_at
                      )}
                    </span>
                  </div>
                  <p
                    className={`truncate text-sm ${
                      unread ? "text-neutral-900" : "text-neutral-500"
                    }`}
                  >
                    {messagePreview(
                      conversation.last_message,
                      user?.id,
                      isGroup
                    )}
                  </p>
                </div>
                {!archived && unread && (
                  <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-sky-500 px-1.5 text-xs font-semibold text-white">
                    {conversation.unread_count}
                  </span>
                )}
                {archived ? (
                  <button
                    type="button"
                    onClick={(e) => unhide(e, conversation.id)}
                    className="shrink-0 rounded-full border border-neutral-300 px-3 py-1 text-xs font-medium text-neutral-600 transition hover:bg-neutral-100"
                  >
                    Unhide
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={(e) => hide(e, conversation.id)}
                    className="hidden shrink-0 rounded-full p-1.5 text-neutral-400 transition hover:bg-neutral-200 hover:text-neutral-700 group-hover:block"
                    aria-label="Hide conversation"
                    title="Hide conversation"
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
                      <path d="M3 3l18 18M10.6 10.6a2 2 0 0 0 2.8 2.8" />
                      <path d="M9.4 5.2A9.3 9.3 0 0 1 12 5c5 0 9 4.5 9 7a12 12 0 0 1-2.2 3M6.2 6.2A12.5 12.5 0 0 0 3 12c0 2.5 4 7 9 7a9 9 0 0 0 3.3-.6" />
                    </svg>
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {showNew && (
        <NewMessageModal
          onClose={() => setShowNew(false)}
          onCreated={(conversation) => {
            setShowNew(false);
            navigate(`/messages/${conversation.id}`);
          }}
        />
      )}
    </div>
  );
}
