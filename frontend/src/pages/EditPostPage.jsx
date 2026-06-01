import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getPost, updatePost } from "../api/posts";
import { useAuth } from "../auth/AuthContext";
import MediaCarousel from "../components/MediaCarousel";
import Spinner from "../components/Spinner";

export default function EditPostPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const fileInput = useRef(null);

  const [post, setPost] = useState(null);
  const [caption, setCaption] = useState("");
  const [hashtags, setHashtags] = useState("");
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await getPost(id);
        if (user && data.author_id !== user.id) {
          navigate(`/p/${id}`, { replace: true });
          return;
        }
        setPost(data);
        setCaption(data.caption || "");
        setHashtags((data.hashtags || []).join(" "));
      } catch {
        setError("Could not load this post.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id, user, navigate]);

  function onPickFiles(event) {
    const picked = Array.from(event.target.files || []);
    if (picked.length) {
      setFiles(picked.slice(0, 10));
    }
    event.target.value = "";
  }

  async function onSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");

    const form = new FormData();
    form.append("caption", caption);
    parseHashtags(hashtags).forEach((tag) => form.append("hashtags", tag));
    files.forEach((file) => form.append("media", file));

    try {
      await updatePost(id, form);
      navigate(`/p/${id}`);
    } catch (err) {
      setError(extractError(err));
      setSaving(false);
    }
  }

  if (loading) return <Spinner label="Loading..." />;
  if (!post) {
    return (
      <div className="rounded-xl border border-neutral-200 bg-white py-16 text-center">
        <p className="text-sm text-neutral-500">{error || "Post not found."}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <h2 className="text-xl font-semibold text-neutral-900">Edit post</h2>

      <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white">
        <MediaCarousel items={post.media_items} />
      </div>

      <form onSubmit={onSubmit} className="space-y-6">
        <div className="space-y-2">
          <label className="block text-sm font-medium text-neutral-700">
            Caption
          </label>
          <textarea
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            rows={3}
            maxLength={2200}
            className="w-full resize-none rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-500"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-neutral-700">
            Hashtags
          </label>
          <input
            type="text"
            value={hashtags}
            onChange={(e) => setHashtags(e.target.value)}
            placeholder="travel sunset food"
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-500"
          />
        </div>

        <div className="space-y-2 rounded-xl border border-neutral-200 bg-white p-4">
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            className="text-sm font-semibold text-sky-500 transition hover:text-sky-600"
          >
            Replace media
          </button>
          <input
            ref={fileInput}
            type="file"
            accept="image/*,video/*"
            multiple
            onChange={onPickFiles}
            className="hidden"
          />
          <p className="text-xs text-neutral-400">
            {files.length > 0
              ? `${files.length} new file(s) will replace the current media.`
              : "Leave empty to keep the current media."}
          </p>
        </div>

        {error && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
            {error}
          </p>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-sky-500 px-5 py-2 text-sm font-semibold text-white transition hover:bg-sky-600 disabled:opacity-60"
          >
            {saving ? "Saving..." : "Save"}
          </button>
          <button
            type="button"
            onClick={() => navigate(`/p/${id}`)}
            className="rounded-lg px-5 py-2 text-sm font-semibold text-neutral-600 transition hover:bg-neutral-100"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

function parseHashtags(value) {
  return value
    .split(/[\s,]+/)
    .map((tag) => tag.trim().replace(/^#/, ""))
    .filter(Boolean);
}

function extractError(err) {
  const data = err.response?.data;
  if (!data) return "Could not save the post.";
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  const firstKey = Object.keys(data)[0];
  if (firstKey) {
    const value = data[firstKey];
    return Array.isArray(value) ? `${firstKey}: ${value[0]}` : `${firstKey}: ${value}`;
  }
  return "Could not save the post.";
}
