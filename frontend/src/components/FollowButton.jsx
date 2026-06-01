import { useEffect, useState } from "react";

import { followUser, unfollowUser } from "../api/social";

export default function FollowButton({
  userId,
  initialFollowing = false,
  onChange,
  size = "md",
}) {
  const [following, setFollowing] = useState(initialFollowing);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setFollowing(initialFollowing);
  }, [initialFollowing]);

  async function toggle() {
    if (busy) return;
    setBusy(true);
    const next = !following;
    try {
      if (following) {
        await unfollowUser(userId);
      } else {
        await followUser(userId);
      }
      setFollowing(next);
      if (onChange) onChange(next);
    } catch {
      // leave the button state unchanged on failure
    } finally {
      setBusy(false);
    }
  }

  const sizeClasses =
    size === "sm" ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm";

  const styleClasses = following
    ? "bg-neutral-100 text-neutral-900 hover:bg-neutral-200"
    : "bg-sky-500 text-white hover:bg-sky-600";

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={busy}
      className={`rounded-lg font-semibold transition disabled:opacity-60 ${sizeClasses} ${styleClasses}`}
    >
      {following ? "Following" : "Follow"}
    </button>
  );
}
