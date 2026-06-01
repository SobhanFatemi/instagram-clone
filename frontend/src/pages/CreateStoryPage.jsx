import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { createStory } from "../api/stories";

export default function CreateStoryPage() {
  const navigate = useNavigate();
  const fileInput = useRef(null);

  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [mediaType, setMediaType] = useState(null);
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function onPickFile(event) {
    const picked = event.target.files[0];
    if (!picked) return;
    setFile(picked);
    setPreview(URL.createObjectURL(picked));
    setMediaType(picked.type.startsWith("video") ? "video" : "image");
    setError("");
  }

  async function onSubmit(event) {
    event.preventDefault();
    if (!file) {
      setError("Please choose a photo or video.");
      return;
    }
    setSaving(true);
    setError("");

    const form = new FormData();
    form.append("media_type", mediaType);
    form.append("file", file);
    if (text.trim()) {
      form.append("text", text.trim());
    }

    try {
      await createStory(form);
      navigate("/");
    } catch (err) {
      setError(extractError(err));
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <h2 className="text-xl font-semibold text-neutral-900">New story</h2>

      <form onSubmit={onSubmit} className="space-y-5">
        <div className="flex flex-col items-center gap-4 rounded-xl border border-neutral-200 bg-white p-4">
          {preview ? (
            <div className="relative w-full max-w-xs overflow-hidden rounded-xl bg-black">
              {mediaType === "video" ? (
                <video src={preview} controls className="max-h-96 w-full" />
              ) : (
                <img src={preview} alt="story preview" className="max-h-96 w-full object-contain" />
              )}
              {text.trim() && (
                <p className="absolute inset-x-0 bottom-6 px-4 text-center text-lg font-semibold text-white drop-shadow">
                  {text.trim()}
                </p>
              )}
            </div>
          ) : (
            <div className="flex h-48 w-full max-w-xs items-center justify-center rounded-xl border border-dashed border-neutral-300 text-sm text-neutral-400">
              No file selected
            </div>
          )}

          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            className="rounded-lg bg-neutral-100 px-4 py-2 text-sm font-semibold text-neutral-900 transition hover:bg-neutral-200"
          >
            {file ? "Choose a different file" : "Choose photo or video"}
          </button>
          <input
            ref={fileInput}
            type="file"
            accept="image/*,video/*"
            onChange={onPickFile}
            className="hidden"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-neutral-700">
            Text (optional)
          </label>
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={255}
            placeholder="Add a caption to your story"
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-500"
          />
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
            {saving ? "Sharing..." : "Share to story"}
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

function extractError(err) {
  const data = err.response?.data;
  if (!data) return "Could not share your story.";
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  const firstKey = Object.keys(data)[0];
  if (firstKey) {
    const value = data[firstKey];
    return Array.isArray(value) ? `${firstKey}: ${value[0]}` : `${firstKey}: ${value}`;
  }
  return "Could not share your story.";
}
