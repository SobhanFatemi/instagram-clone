import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { createPost } from "../api/posts";

export default function CreatePostPage() {
  const navigate = useNavigate();
  const fileInput = useRef(null);

  const [files, setFiles] = useState([]);
  const [caption, setCaption] = useState("");
  const [hashtags, setHashtags] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function onPickFiles(event) {
    const picked = Array.from(event.target.files || []);
    if (!picked.length) return;
    setFiles((current) => {
      const combined = [...current, ...picked];
      if (combined.length > 10) {
        setError("You can upload at most 10 media items.");
        return combined.slice(0, 10);
      }
      setError("");
      return combined;
    });
    event.target.value = "";
  }

  function removeFile(index) {
    setFiles((current) => current.filter((_, i) => i !== index));
  }

  async function onSubmit(event) {
    event.preventDefault();
    if (!files.length) {
      setError("Add at least one photo or video.");
      return;
    }

    setSaving(true);
    setError("");

    const form = new FormData();
    files.forEach((file) => form.append("media", file));
    form.append("caption", caption);
    parseHashtags(hashtags).forEach((tag) => form.append("hashtags", tag));

    try {
      const post = await createPost(form);
      navigate(`/p/${post.id}`);
    } catch (err) {
      setError(extractError(err));
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <h2 className="text-xl font-semibold text-neutral-900">Create new post</h2>

      <form onSubmit={onSubmit} className="space-y-6">
        <div className="rounded-xl border border-dashed border-neutral-300 bg-white p-4">
          {files.length === 0 ? (
            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              className="flex w-full flex-col items-center gap-2 py-10 text-neutral-500 transition hover:text-neutral-700"
            >
              <span className="text-3xl">＋</span>
              <span className="text-sm font-medium">Select photos and videos</span>
            </button>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-2">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="relative aspect-square overflow-hidden rounded-lg bg-neutral-100"
                  >
                    {file.type.startsWith("video") ? (
                      <video
                        src={URL.createObjectURL(file)}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <img
                        src={URL.createObjectURL(file)}
                        alt=""
                        className="h-full w-full object-cover"
                      />
                    )}
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      aria-label="Remove"
                      className="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-black/60 text-xs text-white transition hover:bg-black/80"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
              <button
                type="button"
                onClick={() => fileInput.current?.click()}
                className="text-sm font-semibold text-sky-500 transition hover:text-sky-600"
              >
                Add more
              </button>
            </div>
          )}
          <input
            ref={fileInput}
            type="file"
            accept="image/*,video/*"
            multiple
            onChange={onPickFiles}
            className="hidden"
          />
          <p className="mt-2 text-xs text-neutral-400">
            {files.length}/10 selected
          </p>
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-neutral-700">
            Caption
          </label>
          <textarea
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            rows={3}
            maxLength={2200}
            placeholder="Write a caption..."
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
          <p className="text-xs text-neutral-400">
            Separate tags with spaces or commas.
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
            {saving ? "Sharing..." : "Share"}
          </button>
          <button
            type="button"
            onClick={() => navigate(-1)}
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
  if (!data) return "Could not create the post.";
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  const firstKey = Object.keys(data)[0];
  if (firstKey) {
    const value = data[firstKey];
    return Array.isArray(value) ? `${firstKey}: ${value[0]}` : `${firstKey}: ${value}`;
  }
  return "Could not create the post.";
}
