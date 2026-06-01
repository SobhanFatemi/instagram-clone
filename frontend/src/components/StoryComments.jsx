import { useEffect, useState } from "react";

import {
  createStoryComment,
  deleteStoryComment,
  getStoryComments,
} from "../api/stories";
import Modal from "./Modal";
import Spinner from "./Spinner";
import { timeAgo } from "../lib/time";

export default function StoryComments({
  storyId,
  storyOwnerId,
  currentUserId,
  onClose,
}) {
  const [comments, setComments] = useState([]);
  const [page, setPage] = useState(1);
  const [next, setNext] = useState(null);
  const [loading, setLoading] = useState(true);
  const [text, setText] = useState("");
  const [posting, setPosting] = useState(false);
  const [replyingTo, setReplyingTo] = useState(null);
  const [replyText, setReplyText] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const data = await getStoryComments(storyId, 1);
        if (active) {
          setComments(data.results);
          setNext(data.next);
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [storyId]);

  async function loadMore() {
    if (!next) return;
    const data = await getStoryComments(storyId, page + 1);
    setComments((current) => [...current, ...data.results]);
    setNext(data.next);
    setPage((p) => p + 1);
  }

  async function addComment(event) {
    event.preventDefault();
    const content = text.trim();
    if (!content || posting) return;
    setPosting(true);
    try {
      const created = await createStoryComment(storyId, {
        story: storyId,
        content,
      });
      setComments((current) => [...current, created]);
      setText("");
    } finally {
      setPosting(false);
    }
  }

  async function addReply(parentId) {
    const content = replyText.trim();
    if (!content || posting) return;
    setPosting(true);
    try {
      const created = await createStoryComment(storyId, {
        story: storyId,
        parent: parentId,
        content,
      });
      setComments((current) =>
        current.map((c) =>
          c.id === parentId
            ? { ...c, replies: [...(c.replies || []), created] }
            : c
        )
      );
      setReplyText("");
      setReplyingTo(null);
    } finally {
      setPosting(false);
    }
  }

  async function remove(comment, parentId = null) {
    await deleteStoryComment(comment.id);
    if (parentId === null) {
      setComments((current) => current.filter((c) => c.id !== comment.id));
    } else {
      setComments((current) =>
        current.map((c) =>
          c.id === parentId
            ? { ...c, replies: c.replies.filter((r) => r.id !== comment.id) }
            : c
        )
      );
    }
  }

  function canDelete(comment) {
    return currentUserId === comment.user_id || currentUserId === storyOwnerId;
  }

  return (
    <Modal title="Comments" onClose={onClose}>
      <div className="flex max-h-[70vh] flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
          {loading ? (
            <Spinner label="Loading comments..." />
          ) : comments.length === 0 ? (
            <p className="py-10 text-center text-sm text-neutral-500">
              No comments yet.
            </p>
          ) : (
            comments.map((comment) => (
              <div key={comment.id} className="space-y-2">
                <Row
                  comment={comment}
                  canDelete={canDelete(comment)}
                  onDelete={() => remove(comment)}
                  onReply={() => {
                    setReplyingTo(replyingTo === comment.id ? null : comment.id);
                    setReplyText("");
                  }}
                />

                {comment.replies?.map((reply) => (
                  <div key={reply.id} className="ml-10">
                    <Row
                      comment={reply}
                      canDelete={canDelete(reply)}
                      onDelete={() => remove(reply, comment.id)}
                    />
                  </div>
                ))}

                {replyingTo === comment.id && (
                  <div className="ml-10 flex gap-2">
                    <input
                      type="text"
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      placeholder={`Reply to ${comment.username}`}
                      autoFocus
                      className="flex-1 rounded-lg border border-neutral-300 px-3 py-1.5 text-sm outline-none focus:border-neutral-500"
                    />
                    <button
                      type="button"
                      onClick={() => addReply(comment.id)}
                      disabled={posting || !replyText.trim()}
                      className="text-sm font-semibold text-sky-500 disabled:opacity-50"
                    >
                      Send
                    </button>
                  </div>
                )}
              </div>
            ))
          )}

          {next && (
            <button
              type="button"
              onClick={loadMore}
              className="w-full text-center text-sm font-medium text-neutral-500 hover:text-neutral-700"
            >
              Load more comments
            </button>
          )}
        </div>

        <form
          onSubmit={addComment}
          className="flex gap-2 border-t border-neutral-200 px-4 py-3"
        >
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Add a comment..."
            className="flex-1 rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-500"
          />
          <button
            type="submit"
            disabled={posting || !text.trim()}
            className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-600 disabled:opacity-50"
          >
            Post
          </button>
        </form>
      </div>
    </Modal>
  );
}

function Row({ comment, canDelete, onDelete, onReply }) {
  return (
    <div className="flex items-start justify-between gap-2">
      <p className="text-sm text-neutral-800">
        <span className="font-semibold">{comment.username}</span>{" "}
        {comment.content}
        <span className="ml-2 text-xs text-neutral-400">
          {timeAgo(comment.created_at)}
        </span>
      </p>
      <div className="flex shrink-0 items-center gap-2">
        {onReply && (
          <button
            type="button"
            onClick={onReply}
            className="text-xs font-medium text-neutral-400 hover:text-neutral-600"
          >
            Reply
          </button>
        )}
        {canDelete && (
          <button
            type="button"
            onClick={onDelete}
            className="text-xs font-medium text-red-400 hover:text-red-600"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
