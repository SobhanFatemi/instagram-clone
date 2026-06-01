import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  createComment,
  deleteComment,
  getComments,
  getPost,
} from "../api/posts";
import { useAuth } from "../auth/AuthContext";
import CommentItem from "../components/CommentItem";
import PostCard from "../components/PostCard";
import Spinner from "../components/Spinner";

export default function PostDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();

  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentCount, setCommentCount] = useState(0);
  const [page, setPage] = useState(1);
  const [next, setNext] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [text, setText] = useState("");
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await getPost(id);
        setPost(data);
        setCommentCount(data.comment_count);
        const commentData = await getComments(id, 1);
        setComments(commentData.results);
        setNext(commentData.next);
        setPage(1);
      } catch (err) {
        if (err.response && err.response.status === 404) {
          setError("This post doesn't exist or was removed.");
        } else {
          setError("Could not load this post.");
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  async function loadMoreComments() {
    if (!next) return;
    const data = await getComments(id, page + 1);
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
      const comment = await createComment(id, { content });
      setComments((current) => [...current, comment]);
      setCommentCount((c) => c + 1);
      setText("");
    } finally {
      setPosting(false);
    }
  }

  async function handleReply(parentId, content) {
    const reply = await createComment(id, { content, parent: parentId });
    setComments((current) =>
      current.map((c) =>
        c.id === parentId
          ? { ...c, replies: [...(c.replies || []), reply] }
          : c
      )
    );
    setCommentCount((c) => c + 1);
  }

  async function handleDelete(commentId) {
    if (!window.confirm("Delete this comment?")) return;
    await deleteComment(commentId);
    setComments((current) => removeComment(current, commentId, setCommentCount));
  }

  if (loading) return <Spinner label="Loading post..." />;

  if (error) {
    return (
      <div className="space-y-4">
        <BackLink />
        <div className="rounded-xl border border-neutral-200 bg-white py-16 text-center">
          <p className="text-sm text-neutral-500">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <BackLink />

      <PostCard post={post} onChange={setPost} detail />

      <div className="space-y-4 rounded-xl border border-neutral-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-neutral-900">
          {commentCount} {commentCount === 1 ? "comment" : "comments"}
        </h3>

        {comments.length === 0 ? (
          <p className="py-6 text-center text-sm text-neutral-500">
            No comments yet. Be the first to comment.
          </p>
        ) : (
          <div className="space-y-4">
            {comments.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                currentUserId={user?.id}
                postAuthorId={post.author_id}
                onReply={handleReply}
                onDelete={handleDelete}
              />
            ))}

            {next && (
              <button
                type="button"
                onClick={loadMoreComments}
                className="text-sm font-medium text-neutral-500 hover:text-neutral-700"
              >
                View more comments
              </button>
            )}
          </div>
        )}

        <form onSubmit={addComment} className="flex gap-2 border-t border-neutral-100 pt-4">
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
    </div>
  );
}

function removeComment(comments, commentId, setCommentCount) {
  const top = comments.find((c) => c.id === commentId);
  if (top) {
    setCommentCount((c) => Math.max(0, c - 1 - (top.replies?.length || 0)));
    return comments.filter((c) => c.id !== commentId);
  }

  setCommentCount((c) => Math.max(0, c - 1));
  return comments.map((c) => ({
    ...c,
    replies: (c.replies || []).filter((r) => r.id !== commentId),
  }));
}

function BackLink() {
  return (
    <Link
      to="/"
      className="inline-block text-sm text-neutral-500 transition hover:text-neutral-800"
    >
      &larr; Back
    </Link>
  );
}
