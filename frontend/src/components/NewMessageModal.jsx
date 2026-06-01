import { useEffect, useState } from "react";

import { searchUsers } from "../api/feed";
import {
  createDirectConversation,
  createGroupConversation,
} from "../api/messaging";
import Avatar from "./Avatar";
import Modal from "./Modal";

export default function NewMessageModal({ onClose, onCreated }) {
  const [tab, setTab] = useState("direct");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [selected, setSelected] = useState([]);
  const [title, setTitle] = useState("");
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function pickImage(file) {
    setImagePreview((current) => {
      if (current) URL.revokeObjectURL(current);
      return file ? URL.createObjectURL(file) : null;
    });
    setImage(file);
  }

  useEffect(() => {
    const term = query.trim();
    if (!term) {
      setResults([]);
      return;
    }
    const handle = setTimeout(async () => {
      try {
        setResults(await searchUsers(term));
      } catch {
        setResults([]);
      }
    }, 300);
    return () => clearTimeout(handle);
  }, [query]);

  async function startDirect(user) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const conversation = await createDirectConversation(user.id);
      onCreated(conversation);
    } catch {
      setError("Could not start the conversation.");
      setBusy(false);
    }
  }

  function toggleSelect(user) {
    setSelected((current) =>
      current.some((u) => u.id === user.id)
        ? current.filter((u) => u.id !== user.id)
        : [...current, user]
    );
  }

  async function createGroup() {
    if (busy) return;
    if (!title.trim()) {
      setError("Group name is required.");
      return;
    }
    if (selected.length < 1) {
      setError("Add at least one other member.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("title", title.trim());
      selected.forEach((u) => formData.append("participant_ids", u.id));
      if (image) {
        formData.append("image", image);
      }
      const conversation = await createGroupConversation(formData);
      onCreated(conversation);
    } catch {
      setError("Could not create the group.");
      setBusy(false);
    }
  }

  return (
    <Modal title="New message" onClose={onClose}>
      <div className="flex flex-col">
        <div className="flex border-b border-neutral-200">
          {["direct", "group"].map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => {
                setTab(key);
                setError("");
              }}
              className={`flex-1 px-4 py-2.5 text-sm font-medium capitalize transition ${
                tab === key
                  ? "border-b-2 border-neutral-900 text-neutral-900"
                  : "text-neutral-500 hover:text-neutral-800"
              }`}
            >
              {key === "direct" ? "Direct" : "Group"}
            </button>
          ))}
        </div>

        <div className="space-y-3 p-4">
          {tab === "group" && (
            <>
              <div className="flex flex-col items-center gap-1.5">
                <label className="relative cursor-pointer">
                  {imagePreview ? (
                    <img
                      src={imagePreview}
                      alt="Group"
                      className="h-20 w-20 rounded-full object-cover"
                    />
                  ) : (
                    <span className="flex h-20 w-20 items-center justify-center rounded-full bg-neutral-100 text-neutral-400">
                      <svg
                        width="30"
                        height="30"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.6"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M3 8.5A1.5 1.5 0 0 1 4.5 7h2l1-2h7l1 2h2A1.5 1.5 0 0 1 21 8.5V18a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18Z" />
                        <circle cx="12" cy="13" r="3.2" />
                      </svg>
                    </span>
                  )}
                  <span className="absolute bottom-0 right-0 flex h-7 w-7 items-center justify-center rounded-full border-2 border-white bg-sky-500 text-base font-bold text-white">
                    +
                  </span>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => pickImage(e.target.files?.[0] || null)}
                  />
                </label>
                <span className="text-xs text-neutral-500">Group photo</span>
              </div>

              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Group name"
                className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-neutral-500 focus:outline-none"
              />

              {selected.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {selected.map((u) => (
                    <button
                      key={u.id}
                      type="button"
                      onClick={() => toggleSelect(u)}
                      className="flex items-center gap-1 rounded-full bg-neutral-900 px-2.5 py-1 text-xs font-medium text-white"
                    >
                      {u.username}
                      <span className="text-neutral-300">&times;</span>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search people"
            autoFocus
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-neutral-500 focus:outline-none"
          />

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="max-h-64 space-y-1 overflow-y-auto">
            {results.map((user) => {
              const isSelected = selected.some((u) => u.id === user.id);
              return (
                <button
                  key={user.id}
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    tab === "direct" ? startDirect(user) : toggleSelect(user)
                  }
                  className={`flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left transition hover:bg-neutral-100 ${
                    isSelected ? "bg-neutral-100" : ""
                  }`}
                >
                  <Avatar src={user.avatar} name={user.username} size={40} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-neutral-900">
                      {user.username}
                    </p>
                    {user.display_name && (
                      <p className="truncate text-xs text-neutral-500">
                        {user.display_name}
                      </p>
                    )}
                  </div>
                  {tab === "group" && (
                    <span
                      className={`flex h-5 w-5 items-center justify-center rounded-full border ${
                        isSelected
                          ? "border-neutral-900 bg-neutral-900 text-white"
                          : "border-neutral-300"
                      }`}
                    >
                      {isSelected ? "✓" : ""}
                    </span>
                  )}
                </button>
              );
            })}
            {query.trim() && results.length === 0 && (
              <p className="px-2 py-4 text-center text-sm text-neutral-400">
                No people found.
              </p>
            )}
          </div>

          {tab === "group" && (
            <button
              type="button"
              onClick={createGroup}
              disabled={busy}
              className="w-full rounded-lg bg-neutral-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-neutral-800 disabled:opacity-50"
            >
              {busy ? "Creating…" : "Create group"}
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
}
