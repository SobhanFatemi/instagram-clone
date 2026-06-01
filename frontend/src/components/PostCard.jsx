import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  deletePost,
  likePost,
  savePost,
  unlikePost,
  unsavePost,
} from "../api/posts";
import { useAuth } from "../auth/AuthContext";
import { timeAgo } from "../lib/time";
import Avatar from "./Avatar";
import MediaCarousel from "./MediaCarousel";

export default function PostCard({ post, onChange, onDeleted, detail = false }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const menuRef = useRef(null);

  const [liked, setLiked] = useState(post.is_liked);
  const [likeCount, setLikeCount] = useState(post.like_count);
  const [saved, setSaved] = useState(post.is_saved);
  const [busy, setBusy] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setLiked(post.is_liked);
    setLikeCount(post.like_count);
    setSaved(post.is_saved);
  }, [post.id, post.is_liked, post.like_count, post.is_saved]);

  useEffect(() => {
    function onClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const isAuthor = user && post.author_id === user.id;

  async function toggleLike() {
    if (busy) return;
    setBusy(true);
    const next = !liked;
    const nextCount = likeCount + (next ? 1 : -1);
    setLiked(next);
    setLikeCount(nextCount);
    try {
      if (next) {
        await likePost(post.id);
      } else {
        await unlikePost(post.id);
      }
      if (onChange) onChange({ ...post, is_liked: next, like_count: nextCount });
    } catch {
      setLiked(!next);
      setLikeCount(likeCount);
    } finally {
      setBusy(false);
    }
  }

  async function toggleSave() {
    if (busy) return;
    setBusy(true);
    const next = !saved;
    setSaved(next);
    try {
      if (next) {
        await savePost(post.id);
      } else {
        await unsavePost(post.id);
      }
      if (onChange) onChange({ ...post, is_saved: next });
    } catch {
      setSaved(!next);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    setMenuOpen(false);
    if (!window.confirm("Delete this post?")) return;
    try {
      await deletePost(post.id);
      if (onDeleted) {
        onDeleted(post.id);
      } else {
        navigate("/profile");
      }
    } catch {
      window.alert("Could not delete the post.");
    }
  }

  return (
    <article className="overflow-hidden rounded-xl border border-neutral-200 bg-white">
      <div className="flex items-center gap-3 px-4 py-3">
        <Link to={`/u/${post.author_username}`}>
          <Avatar src={post.author_avatar} name={post.author_username} size={36} />
        </Link>
        <div className="min-w-0 flex-1">
          <Link
            to={`/u/${post.author_username}`}
            className="block truncate text-sm font-semibold text-neutral-900 hover:underline"
          >
            {post.author_username}
          </Link>
          {post.author_display_name && (
            <p className="truncate text-xs text-neutral-500">
              {post.author_display_name}
            </p>
          )}
        </div>

        {isAuthor && (
          <div ref={menuRef} className="relative">
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              aria-label="Post options"
              className="rounded-full px-2 py-1 text-lg leading-none text-neutral-600 transition hover:bg-neutral-100"
            >
              ⋯
            </button>
            {menuOpen && (
              <div className="absolute right-0 z-10 mt-1 w-36 overflow-hidden rounded-lg border border-neutral-200 bg-white shadow-lg">
                <Link
                  to={`/p/${post.id}/edit`}
                  className="block px-4 py-2 text-left text-sm text-neutral-800 transition hover:bg-neutral-100"
                >
                  Edit
                </Link>
                <button
                  type="button"
                  onClick={handleDelete}
                  className="block w-full px-4 py-2 text-left text-sm text-red-600 transition hover:bg-red-50"
                >
                  Delete
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <MediaCarousel items={post.media_items} />

      <div className="flex items-center gap-4 px-4 pb-1 pt-3">
        <button
          type="button"
          onClick={toggleLike}
          disabled={busy}
          aria-label={liked ? "Unlike" : "Like"}
          className="transition hover:opacity-70 disabled:opacity-60"
        >
          <HeartIcon filled={liked} />
        </button>
        <Link to={`/p/${post.id}`} aria-label="Comments" className="hover:opacity-70">
          <CommentIcon />
        </Link>
        <button
          type="button"
          onClick={toggleSave}
          disabled={busy}
          aria-label={saved ? "Unsave" : "Save"}
          className="ml-auto transition hover:opacity-70 disabled:opacity-60"
        >
          <BookmarkIcon filled={saved} />
        </button>
      </div>

      <div className="space-y-1 px-4 pb-4">
        <p className="text-sm font-semibold text-neutral-900">
          {likeCount} {likeCount === 1 ? "like" : "likes"}
        </p>

        {post.caption && (
          <p className="whitespace-pre-line text-sm text-neutral-800">
            <Link
              to={`/u/${post.author_username}`}
              className="font-semibold hover:underline"
            >
              {post.author_username}
            </Link>{" "}
            {post.caption}
          </p>
        )}

        {post.hashtags && post.hashtags.length > 0 && (
          <p className="text-sm text-sky-600">
            {post.hashtags.map((tag) => `#${tag}`).join(" ")}
          </p>
        )}

        {!detail && post.comment_count > 0 && (
          <Link
            to={`/p/${post.id}`}
            className="block text-sm text-neutral-500 hover:underline"
          >
            View all {post.comment_count} comments
          </Link>
        )}

        <p className="pt-1 text-xs uppercase tracking-wide text-neutral-400">
          {timeAgo(post.created_at)}
          {detail && ` · ${post.view_count} views`}
        </p>
      </div>
    </article>
  );
}

function HeartIcon({ filled }) {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill={filled ? "#ef4444" : "none"}
      stroke={filled ? "#ef4444" : "currentColor"}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 20s-7-4.6-9.3-9A4.7 4.7 0 0 1 12 6a4.7 4.7 0 0 1 9.3 5c-2.3 4.4-9.3 9-9.3 9Z" />
    </svg>
  );
}

function CommentIcon() {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 11.5a8 8 0 0 1-11.5 7.2L4 20l1.3-4.5A8 8 0 1 1 21 11.5Z" />
    </svg>
  );
}

function BookmarkIcon({ filled }) {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M6 4h12v16l-6-4-6 4V4Z" />
    </svg>
  );
}
