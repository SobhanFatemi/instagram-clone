import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { getMe, updateMe } from "../api/accounts";
import { getMyProfile, updateMyProfile } from "../api/profiles";
import { useAuth } from "../auth/AuthContext";
import Avatar from "../components/Avatar";
import Spinner from "../components/Spinner";
import { mediaUrl } from "../lib/media";

export default function EditProfilePage() {
  const navigate = useNavigate();
  const fileInput = useRef(null);
  const { refreshUser } = useAuth();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [username, setUsername] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [contactEmail, setContactEmail] = useState(null);
  const [contactPhone, setContactPhone] = useState(null);
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [isPrivate, setIsPrivate] = useState(false);
  const [currentAvatar, setCurrentAvatar] = useState(null);
  const [avatarFile, setAvatarFile] = useState(null);
  const [avatarPreview, setAvatarPreview] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const profile = await getMyProfile();
        setUsername(profile.username || "");
        setDisplayName(profile.display_name || "");
        setBio(profile.bio || "");
        setIsPrivate(profile.is_private);
        setCurrentAvatar(profile.avatar);
        const me = await getMe();
        setFirstName(me.first_name || "");
        setLastName(me.last_name || "");
        setContactEmail(me.email || null);
        setContactPhone(me.phone_number || null);
      } catch {
        setError("Could not load your profile.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function onPickAvatar(event) {
    const file = event.target.files[0];
    if (!file) return;
    setAvatarFile(file);
    setAvatarPreview(URL.createObjectURL(file));
  }

  async function onSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");

    const form = new FormData();
    form.append("display_name", displayName);
    form.append("bio", bio);
    form.append("is_private", isPrivate ? "true" : "false");
    if (avatarFile) {
      form.append("avatar", avatarFile);
    }

    try {
      await updateMe({
        username: username.trim(),
        first_name: firstName,
        last_name: lastName,
      });
      await updateMyProfile(form);
      await refreshUser();
      navigate("/profile");
    } catch (err) {
      setError(extractError(err));
      setSaving(false);
    }
  }

  if (loading) return <Spinner label="Loading..." />;

  const previewSrc = avatarPreview || mediaUrl(currentAvatar);

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-neutral-900">Edit profile</h2>
        <div className="flex items-center gap-4">
          <Link
            to="/accounts/contact"
            className="text-sm font-medium text-neutral-500 transition hover:text-neutral-800"
          >
            Email & phone
          </Link>
          <Link
            to="/accounts/blocked"
            className="text-sm font-medium text-neutral-500 transition hover:text-neutral-800"
          >
            Blocked accounts
          </Link>
        </div>
      </div>

      {(!contactEmail || !contactPhone) && (
        <Link
          to="/accounts/contact"
          className="block rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-700 transition hover:bg-amber-100"
        >
          {!contactEmail && !contactPhone
            ? "Add an email or phone number to secure your account."
            : !contactEmail
            ? "You haven't added an email yet. Add one →"
            : "You haven't added a phone number yet. Add one →"}
        </Link>
      )}

      <form onSubmit={onSubmit} className="space-y-6">
        <div className="flex items-center gap-4 rounded-xl border border-neutral-200 bg-white p-4">
          {previewSrc ? (
            <img
              src={previewSrc}
              alt="avatar preview"
              className="h-16 w-16 rounded-full object-cover"
            />
          ) : (
            <Avatar name={displayName || "?"} size={64} />
          )}
          <div>
            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              className="text-sm font-semibold text-sky-500 transition hover:text-sky-600"
            >
              Change photo
            </button>
            <p className="mt-1 text-xs text-neutral-400">JPG or PNG.</p>
          </div>
          <input
            ref={fileInput}
            type="file"
            accept="image/*"
            onChange={onPickAvatar}
            className="hidden"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-neutral-700">
            Username
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            maxLength={150}
            placeholder="username"
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-500"
          />
          {/^user_\d{6}$/.test(username.trim()) && (
            <p className="text-xs text-amber-600">
              This is an auto-generated username. Pick something memorable so
              people can find you.
            </p>
          )}
        </div>

        <div className="flex gap-3">
          <div className="flex-1 space-y-2">
            <label className="block text-sm font-medium text-neutral-700">
              First name
            </label>
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              maxLength={150}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-500"
            />
          </div>
          <div className="flex-1 space-y-2">
            <label className="block text-sm font-medium text-neutral-700">
              Last name
            </label>
            <input
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              maxLength={150}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-500"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-neutral-700">
            Display name
          </label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            maxLength={150}
            placeholder="Your name"
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-500"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-neutral-700">Bio</label>
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            rows={4}
            maxLength={1000}
            placeholder="Tell people about yourself"
            className="w-full resize-none rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-500"
          />
          <p className="text-right text-xs text-neutral-400">{bio.length}/1000</p>
        </div>

        <label className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white p-4">
          <span>
            <span className="block text-sm font-medium text-neutral-900">
              Private account
            </span>
            <span className="block text-xs text-neutral-500">
              Only followers can see your posts.
            </span>
          </span>
          <input
            type="checkbox"
            checked={isPrivate}
            onChange={(e) => setIsPrivate(e.target.checked)}
            className="h-5 w-5 accent-sky-500"
          />
        </label>

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
            onClick={() => navigate("/profile")}
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
  if (!data) return "Could not save your profile.";
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  const firstKey = Object.keys(data)[0];
  if (firstKey) {
    const value = data[firstKey];
    return Array.isArray(value) ? `${firstKey}: ${value[0]}` : `${firstKey}: ${value}`;
  }
  return "Could not save your profile.";
}
