import { useState } from "react";
import { Link } from "react-router-dom";

import { timeAgo } from "../lib/time";
import Avatar from "./Avatar";

export default function CommentItem({
  comment,
  currentUserId,
  postAuthorId,
  onReply,
  onDelete,
  isReply = false,
}) {
  const [showReply, setShowReply] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [sending, setSending] = useState(false);

  const author = comment.author || {};
  const canDelete =
    currentUserId === author.id || currentUserId === postAuthorId;

  async function submitReply(event) {
    event.preventDefault();
    const text = replyText.trim();
    if (!text || sending) return;
    setSending(true);
    try {
      await onReply(comment.id, text);
      setReplyText("");
      setShowReply(false);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className={isReply ? "pl-11" : ""}>
      <div className="flex gap-3">
        <Link to={`/u/${author.username}`}>
          <Avatar
            src={author.avatar}
            name={author.username}
            size={isReply ? 28 : 36}
          />
        </Link>
        <div className="min-w-0 flex-1">
          <p className="text-sm text-neutral-800">
            <Link
              to={`/u/${author.username}`}
              className="font-semibold hover:underline"
            >
              {author.username}
            </Link>{" "}
            {comment.content}
          </p>
          <div className="mt-1 flex items-center gap-4 text-xs text-neutral-400">
            <span>{timeAgo(comment.created_at)}</span>
            {!isReply && (
              <button
                type="button"
                onClick={() => setShowReply((v) => !v)}
                className="font-medium hover:text-neutral-600"
              >
                Reply
              </button>
            )}
            {canDelete && (
              <button
                type="button"
                onClick={() => onDelete(comment.id)}
                className="font-medium hover:text-red-500"
              >
                Delete
              </button>
            )}
          </div>

          {showReply && (
            <form onSubmit={submitReply} className="mt-2 flex gap-2">
              <input
                type="text"
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder={`Reply to ${author.username}...`}
                className="flex-1 rounded-lg border border-neutral-300 px-3 py-1.5 text-sm outline-none focus:border-neutral-500"
              />
              <button
                type="submit"
                disabled={sending || !replyText.trim()}
                className="text-sm font-semibold text-sky-500 disabled:opacity-50"
              >
                Post
              </button>
            </form>
          )}
        </div>
      </div>

      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-3 space-y-3">
          {comment.replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              currentUserId={currentUserId}
              postAuthorId={postAuthorId}
              onReply={onReply}
              onDelete={onDelete}
              isReply
            />
          ))}
        </div>
      )}
    </div>
  );
}
