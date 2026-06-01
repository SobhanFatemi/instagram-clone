import { useEffect, useRef, useState } from "react";

import {
  createStoryComment,
  deleteStory,
  getStoryViewers,
  markStoryViewed,
} from "../api/stories";
import Avatar from "./Avatar";
import Modal from "./Modal";
import Spinner from "./Spinner";
import StoryComments from "./StoryComments";
import { mediaUrl } from "../lib/media";
import { timeAgo } from "../lib/time";

const STORY_DURATION = 5000;

export default function StoryViewer({
  groups,
  startIndex,
  currentUserId,
  onClose,
  onViewed,
  onDeleted,
}) {
  const [groupIndex, setGroupIndex] = useState(startIndex);
  const [storyIndex, setStoryIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [panel, setPanel] = useState(null);
  const [viewers, setViewers] = useState(null);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const [replySent, setReplySent] = useState(false);
  const videoRef = useRef(null);

  const group = groups[groupIndex];
  const stories = group ? group.stories : [];
  const story = stories[storyIndex];
  const isOwn = group && group.user_id === currentUserId;

  function goNext() {
    if (storyIndex < stories.length - 1) {
      setStoryIndex((i) => i + 1);
    } else if (groupIndex < groups.length - 1) {
      setGroupIndex((g) => g + 1);
      setStoryIndex(0);
    } else {
      onClose();
    }
  }

  function goPrev() {
    if (storyIndex > 0) {
      setStoryIndex((i) => i - 1);
    } else if (groupIndex > 0) {
      const prevGroup = groups[groupIndex - 1];
      setGroupIndex((g) => g - 1);
      setStoryIndex(prevGroup.stories.length - 1);
    }
  }

  useEffect(() => {
    setProgress(0);
    setReply("");
    setReplySent(false);
  }, [groupIndex, storyIndex]);

  useEffect(() => {
    if (!story || isOwn) return;
    markStoryViewed(story.id).catch(() => {});
    if (onViewed) onViewed(story.id);
  }, [story?.id]);

  useEffect(() => {
    if (!story || story.media_type === "video" || panel) return;
    const start = Date.now();
    const id = setInterval(() => {
      const pct = Math.min(100, ((Date.now() - start) / STORY_DURATION) * 100);
      setProgress(pct);
      if (pct >= 100) {
        clearInterval(id);
        goNext();
      }
    }, 50);
    return () => clearInterval(id);
  }, [story?.id, panel]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (panel) {
      video.pause();
    } else {
      video.play().catch(() => {});
    }
  }, [panel, story?.id]);

  useEffect(() => {
    function onKey(event) {
      if (event.key === "ArrowRight") goNext();
      else if (event.key === "ArrowLeft") goPrev();
      else if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  async function openViewers() {
    setPanel("viewers");
    setViewers(null);
    try {
      setViewers(await getStoryViewers(story.id));
    } catch {
      setViewers([]);
    }
  }

  async function sendReply(event) {
    event.preventDefault();
    const content = reply.trim();
    if (!content || sending) return;
    setSending(true);
    try {
      await createStoryComment(story.id, { story: story.id, content });
      setReply("");
      setReplySent(true);
    } finally {
      setSending(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm("Delete this story?")) return;
    await deleteStory(story.id);
    if (onDeleted) onDeleted(story.id);
    onClose();
  }

  if (!story) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4">
      <div className="relative flex h-full max-h-[92vh] w-full max-w-md flex-col">
        <div className="flex gap-1 px-1">
          {stories.map((item, i) => (
            <div
              key={item.id}
              className="h-0.5 flex-1 overflow-hidden rounded-full bg-white/30"
            >
              <div
                className="h-full bg-white"
                style={{
                  width:
                    i < storyIndex
                      ? "100%"
                      : i === storyIndex
                      ? `${progress}%`
                      : "0%",
                }}
              />
            </div>
          ))}
        </div>

        <div className="flex items-center gap-3 px-1 py-2 text-white">
          <Avatar name={group.username} size={32} />
          <span className="text-sm font-semibold">{group.username}</span>
          <span className="text-xs text-white/70">
            {timeAgo(story.created_at)}
          </span>
          <div className="ml-auto flex items-center gap-4">
            {isOwn && (
              <button
                type="button"
                onClick={handleDelete}
                className="text-sm text-white/80 transition hover:text-white"
              >
                Delete
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="text-xl leading-none text-white/80 transition hover:text-white"
              aria-label="Close"
            >
              &times;
            </button>
          </div>
        </div>

        <div className="relative flex-1 overflow-hidden rounded-lg bg-black">
          {story.media_type === "video" ? (
            <video
              ref={videoRef}
              src={mediaUrl(story.file)}
              muted
              playsInline
              autoPlay
              onTimeUpdate={(e) => {
                const v = e.currentTarget;
                if (v.duration) setProgress((v.currentTime / v.duration) * 100);
              }}
              onEnded={goNext}
              className="h-full w-full object-contain"
            />
          ) : (
            <img
              src={mediaUrl(story.file)}
              alt=""
              className="h-full w-full object-contain"
            />
          )}

          {story.text && (
            <p className="pointer-events-none absolute inset-x-0 bottom-16 px-6 text-center text-lg font-semibold text-white drop-shadow">
              {story.text}
            </p>
          )}

          <button
            type="button"
            aria-label="Previous"
            onClick={goPrev}
            className="absolute left-0 top-0 h-full w-1/3"
          />
          <button
            type="button"
            aria-label="Next"
            onClick={goNext}
            className="absolute right-0 top-0 h-full w-2/3"
          />
        </div>

        <div className="px-1 py-3">
          {isOwn ? (
            <div className="flex items-center gap-5 text-sm font-medium text-white">
              <button
                type="button"
                onClick={openViewers}
                className="transition hover:text-white/80"
              >
                Seen by {story.views_count}
              </button>
              <button
                type="button"
                onClick={() => setPanel("comments")}
                className="transition hover:text-white/80"
              >
                Comments
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <form onSubmit={sendReply} className="flex flex-1 items-center gap-2">
                <input
                  type="text"
                  value={reply}
                  onChange={(e) => setReply(e.target.value)}
                  placeholder="Reply to story..."
                  className="flex-1 rounded-full border border-white/40 bg-transparent px-4 py-2 text-sm text-white placeholder-white/60 outline-none focus:border-white"
                />
                <button
                  type="submit"
                  disabled={sending || !reply.trim()}
                  className="text-sm font-semibold text-white disabled:opacity-40"
                >
                  Send
                </button>
              </form>
              <button
                type="button"
                onClick={() => setPanel("comments")}
                className="text-sm font-semibold text-white"
              >
                Comments
              </button>
            </div>
          )}
          {replySent && (
            <p className="mt-1 px-1 text-xs text-white/70">Reply sent &check;</p>
          )}
        </div>
      </div>

      {panel === "comments" && (
        <StoryComments
          storyId={story.id}
          storyOwnerId={group.user_id}
          currentUserId={currentUserId}
          onClose={() => setPanel(null)}
        />
      )}

      {panel === "viewers" && (
        <Modal title="Viewers" onClose={() => setPanel(null)}>
          {viewers === null ? (
            <Spinner label="Loading viewers..." />
          ) : viewers.length === 0 ? (
            <p className="py-10 text-center text-sm text-neutral-500">
              No views yet.
            </p>
          ) : (
            <ul className="divide-y divide-neutral-100">
              {viewers.map((v) => (
                <li
                  key={v.viewer_id}
                  className="flex items-center gap-3 px-4 py-3"
                >
                  <Avatar name={v.username} size={36} />
                  <span className="text-sm font-medium text-neutral-900">
                    {v.username}
                  </span>
                  <span className="ml-auto text-xs text-neutral-400">
                    {timeAgo(v.created_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Modal>
      )}
    </div>
  );
}
