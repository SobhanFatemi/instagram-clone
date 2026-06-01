import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  deleteMessageForEveryone,
  deleteMessageForMe,
  getConversation,
  getConversationMessages,
  hideConversation,
  markConversationRead,
  sendMessage,
} from "../api/messaging";
import { useAuth } from "../auth/AuthContext";
import Avatar from "../components/Avatar";
import Spinner from "../components/Spinner";
import {
  conversationAvatar,
  conversationTitle,
  otherParticipant,
} from "../lib/conversation";
import { mediaUrl } from "../lib/media";
import { timeAgo } from "../lib/time";

const POLL_INTERVAL = 4000;

function formatSize(bytes) {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ConversationPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [conversation, setConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [text, setText] = useState("");
  const [attachment, setAttachment] = useState(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [menuId, setMenuId] = useState(null);
  const [showMembers, setShowMembers] = useState(false);

  const bottomRef = useRef(null);
  const lastIdRef = useRef(null);
  const markedRef = useRef(null);

  const isGroup = conversation?.conversation_type === "group";

  const loadMessages = useCallback(async () => {
    try {
      const data = await getConversationMessages(id);
      setMessages(data);

      const latest = data[data.length - 1];
      if (latest && latest.id !== markedRef.current) {
        markedRef.current = latest.id;
        markConversationRead(id, latest.id).catch(() => {});
      }
    } catch {
      /* keep current */
    }
  }, [id]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    lastIdRef.current = null;
    markedRef.current = null;
    (async () => {
      try {
        setConversation(await getConversation(id));
      } catch {
        navigate("/messages", { replace: true });
        return;
      }
      await loadMessages();
      if (active) setLoading(false);
    })();
    const timer = setInterval(loadMessages, POLL_INTERVAL);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [id, loadMessages, navigate]);

  useEffect(() => {
    const latest = messages[messages.length - 1];
    if (latest && latest.id !== lastIdRef.current) {
      lastIdRef.current = latest.id;
      bottomRef.current?.scrollIntoView({ block: "end" });
    }
  }, [messages]);

  async function handleSend(event) {
    event.preventDefault();
    if (sending) return;
    const trimmed = text.trim();
    if (!trimmed && !attachment) return;

    setSending(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("conversation", id);
      if (attachment) {
        const mime = attachment.type || "";
        const type = mime.startsWith("image")
          ? "image"
          : mime.startsWith("video")
            ? "video"
            : "file";
        formData.append("message_type", type);
        formData.append("attachment", attachment);
        if (trimmed) formData.append("text", trimmed);
      } else {
        formData.append("message_type", "text");
        formData.append("text", trimmed);
      }
      await sendMessage(formData);
      setText("");
      setAttachment(null);
      await loadMessages();
    } catch {
      setError("Message could not be sent.");
    } finally {
      setSending(false);
    }
  }

  async function removeForMe(messageId) {
    setMenuId(null);
    try {
      await deleteMessageForMe(messageId);
      await loadMessages();
    } catch {
      /* ignore */
    }
  }

  async function removeForEveryone(messageId) {
    setMenuId(null);
    try {
      await deleteMessageForEveryone(messageId);
      await loadMessages();
    } catch {
      /* ignore */
    }
  }

  async function hide() {
    try {
      await hideConversation(id);
    } catch {
      /* ignore */
    }
    navigate("/messages");
  }

  if (loading) return <Spinner />;

  const header = conversationAvatar(conversation, user?.id);
  const title = conversationTitle(conversation, user?.id);
  const other = isGroup ? null : otherParticipant(conversation, user?.id);
  const memberCount = conversation?.participants?.length || 0;

  const lastOwn = [...messages]
    .reverse()
    .find((m) => m.sender?.id === user?.id && !m.deleted_for_everyone);

  return (
    <div className="flex h-[calc(100dvh-11rem)] flex-col overflow-hidden rounded-xl border border-neutral-200 bg-white md:h-[calc(100vh-7rem)]">
      <header className="flex items-center gap-3 border-b border-neutral-200 px-3 py-2.5">
        <button
          type="button"
          onClick={() => navigate("/messages")}
          className="rounded-full p-1.5 text-neutral-500 transition hover:bg-neutral-100"
          aria-label="Back"
        >
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m15 18-6-6 6-6" />
          </svg>
        </button>

        <Avatar src={header.src} name={header.name} size={40} />
        <div className="min-w-0 flex-1">
          {other ? (
            <Link
              to={`/u/${other.username}`}
              className="truncate text-sm font-semibold text-neutral-900 hover:underline"
            >
              {title}
            </Link>
          ) : (
            <button
              type="button"
              onClick={() => setShowMembers((v) => !v)}
              className="block truncate text-left text-sm font-semibold text-neutral-900"
            >
              {title}
            </button>
          )}
          <p className="truncate text-xs text-neutral-400">
            {isGroup ? `${memberCount} members` : `@${other?.username}`}
          </p>
        </div>

        <button
          type="button"
          onClick={hide}
          className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-neutral-500 transition hover:bg-neutral-100"
          title="Hide conversation"
        >
          Hide
        </button>
      </header>

      {isGroup && showMembers && (
        <div className="border-b border-neutral-200 bg-neutral-50 px-4 py-3">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-400">
            Members
          </p>
          <ul className="flex flex-wrap gap-3">
            {conversation.participants.map((p) => (
              <li key={p.id} className="flex items-center gap-2">
                <Avatar
                  src={p.user.avatar}
                  name={p.user.username}
                  size={28}
                />
                <span className="text-sm text-neutral-700">
                  {p.user.username}
                  {p.is_admin && (
                    <span className="ml-1 text-xs text-sky-600">admin</span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {messages.length === 0 && (
          <p className="py-10 text-center text-sm text-neutral-400">
            No messages yet. Say hello!
          </p>
        )}

        {messages.map((message) => {
          const mine = message.sender?.id === user?.id;
          return (
            <MessageBubble
              key={message.id}
              message={message}
              mine={mine}
              isGroup={isGroup}
              menuOpen={menuId === message.id}
              onToggleMenu={() =>
                setMenuId((v) => (v === message.id ? null : message.id))
              }
              onDeleteForMe={() => removeForMe(message.id)}
              onDeleteForEveryone={() => removeForEveryone(message.id)}
              isLastOwn={lastOwn && lastOwn.id === message.id}
            />
          );
        })}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={handleSend}
        className="border-t border-neutral-200 px-3 py-2.5"
      >
        {attachment && (
          <div className="mb-2 flex items-center gap-2 rounded-lg bg-neutral-100 px-3 py-1.5 text-xs text-neutral-600">
            <span className="truncate">{attachment.name}</span>
            <button
              type="button"
              onClick={() => setAttachment(null)}
              className="ml-auto text-neutral-400 hover:text-neutral-700"
            >
              Remove
            </button>
          </div>
        )}
        {error && <p className="mb-2 text-xs text-red-600">{error}</p>}
        <div className="flex items-center gap-2">
          <label
            className="cursor-pointer rounded-full p-2 text-neutral-500 transition hover:bg-neutral-100"
            title="Attach file"
          >
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 12.5 12.5 21a5 5 0 0 1-7-7l8.5-8.5a3.3 3.3 0 0 1 4.7 4.7L10 18.4a1.7 1.7 0 0 1-2.4-2.4l7.8-7.8" />
            </svg>
            <input
              type="file"
              className="hidden"
              onChange={(e) => setAttachment(e.target.files?.[0] || null)}
            />
          </label>
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Message…"
            className="flex-1 rounded-full border border-neutral-300 px-4 py-2 text-sm focus:border-neutral-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={sending || (!text.trim() && !attachment)}
            className="rounded-full bg-sky-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-600 disabled:opacity-40"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}

function MessageBubble({
  message,
  mine,
  isGroup,
  menuOpen,
  onToggleMenu,
  onDeleteForMe,
  onDeleteForEveryone,
  isLastOwn,
}) {
  const deleted = message.deleted_for_everyone;
  const url = mediaUrl(message.attachment);

  return (
    <div className={`group flex flex-col ${mine ? "items-end" : "items-start"}`}>
      {isGroup && !mine && (
        <span className="mb-0.5 ml-1 text-xs font-medium text-neutral-500">
          {message.sender?.username}
        </span>
      )}
      <div className="flex max-w-[80%] items-center gap-1.5">
        {mine && !deleted && (
          <div className="relative">
            <button
              type="button"
              onClick={onToggleMenu}
              className="hidden rounded-full p-1 text-neutral-400 transition hover:bg-neutral-100 group-hover:block"
              aria-label="Message options"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="5" cy="12" r="1.6" />
                <circle cx="12" cy="12" r="1.6" />
                <circle cx="19" cy="12" r="1.6" />
              </svg>
            </button>
            {menuOpen && (
              <div className="absolute right-0 top-7 z-10 w-44 overflow-hidden rounded-lg border border-neutral-200 bg-white py-1 text-sm shadow-lg">
                <button
                  type="button"
                  onClick={onDeleteForEveryone}
                  className="block w-full px-3 py-2 text-left text-red-600 transition hover:bg-neutral-50"
                >
                  Delete for everyone
                </button>
                <button
                  type="button"
                  onClick={onDeleteForMe}
                  className="block w-full px-3 py-2 text-left text-neutral-700 transition hover:bg-neutral-50"
                >
                  Delete for me
                </button>
              </div>
            )}
          </div>
        )}

        <div
          className={`rounded-2xl px-3.5 py-2 text-sm ${
            mine
              ? "bg-sky-500 text-white"
              : "bg-neutral-100 text-neutral-900"
          } ${deleted ? "italic opacity-70" : ""}`}
        >
          {deleted ? (
            "This message was deleted"
          ) : message.message_type === "story_reply" ? (
            <div>
              <div
                className={`mb-1 border-l-2 pl-2 text-xs ${
                  mine ? "border-white/50 text-white/80" : "border-neutral-300 text-neutral-500"
                }`}
              >
                ↩ Replied to a story
              </div>
              {message.text}
            </div>
          ) : message.message_type === "image" && url ? (
            <img
              src={url}
              alt="attachment"
              className="max-h-72 rounded-lg"
            />
          ) : message.message_type === "video" && url ? (
            <video src={url} controls className="max-h-72 rounded-lg" />
          ) : message.message_type === "file" && url ? (
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 underline"
            >
              <span>📎 {message.file_name || "Download file"}</span>
              {message.file_size ? (
                <span className="opacity-70">
                  ({formatSize(message.file_size)})
                </span>
              ) : null}
            </a>
          ) : (
            <span className="whitespace-pre-wrap break-words">
              {message.text}
            </span>
          )}
          {message.text &&
            (message.message_type === "image" ||
              message.message_type === "video") && (
              <p className="mt-1 whitespace-pre-wrap break-words">
                {message.text}
              </p>
            )}
        </div>

        {!mine && !deleted && (
          <div className="relative">
            <button
              type="button"
              onClick={onToggleMenu}
              className="hidden rounded-full p-1 text-neutral-400 transition hover:bg-neutral-100 group-hover:block"
              aria-label="Message options"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="5" cy="12" r="1.6" />
                <circle cx="12" cy="12" r="1.6" />
                <circle cx="19" cy="12" r="1.6" />
              </svg>
            </button>
            {menuOpen && (
              <div className="absolute left-0 top-7 z-10 w-40 overflow-hidden rounded-lg border border-neutral-200 bg-white py-1 text-sm shadow-lg">
                <button
                  type="button"
                  onClick={onDeleteForMe}
                  className="block w-full px-3 py-2 text-left text-neutral-700 transition hover:bg-neutral-50"
                >
                  Delete for me
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <span className="mt-0.5 px-1 text-[11px] text-neutral-400">
        {timeAgo(message.created_at)}
        {isLastOwn && <SeenStatus message={message} />}
      </span>
    </div>
  );
}

function SeenStatus({ message }) {
  const statuses = message.recipient_statuses || [];
  if (statuses.length === 0) return null;

  const seen = statuses.filter((s) => s.seen_at).length;
  const delivered = statuses.filter((s) => s.delivered_at).length;

  let label;
  if (seen === statuses.length) {
    label = statuses.length === 1 ? "Seen" : "Seen by all";
  } else if (seen > 0) {
    label = `Seen by ${seen}`;
  } else if (delivered > 0) {
    label = "Delivered";
  } else {
    label = "Sent";
  }

  return <span className="ml-1.5 text-sky-500">· {label}</span>;
}
