import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getStoryFeed } from "../api/stories";
import { useAuth } from "../auth/AuthContext";
import Avatar from "./Avatar";
import StoryViewer from "./StoryViewer";

export default function StoriesTray() {
  const { user } = useAuth();
  const [groups, setGroups] = useState([]);
  const [openIndex, setOpenIndex] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        setGroups(await getStoryFeed());
      } catch {
        setGroups([]);
      }
    }
    load();
  }, []);

  const myGroup = groups.find((g) => g.user_id === user?.id) || null;
  const otherGroups = groups.filter((g) => g.user_id !== user?.id);
  const orderedGroups = myGroup ? [myGroup, ...otherGroups] : otherGroups;

  function hasUnviewed(group) {
    return group.stories.some((s) => !s.is_viewed);
  }

  function markViewed(storyId) {
    setGroups((current) =>
      current.map((g) => ({
        ...g,
        stories: g.stories.map((s) =>
          s.id === storyId ? { ...s, is_viewed: true } : s
        ),
      }))
    );
  }

  async function refresh() {
    try {
      setGroups(await getStoryFeed());
    } catch {
      /* keep current */
    }
  }

  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-3">
      <div className="flex gap-4 overflow-x-auto">
        <div className="flex w-16 shrink-0 flex-col items-center gap-1">
          <button
            type="button"
            onClick={() => myGroup && setOpenIndex(0)}
            className="relative"
          >
            <span
              className={`flex rounded-full p-[2px] ${
                myGroup && hasUnviewed(myGroup)
                  ? "bg-gradient-to-tr from-amber-400 via-pink-500 to-purple-600"
                  : "bg-neutral-200"
              }`}
            >
              <span className="rounded-full border-2 border-white">
                <Avatar name={user?.username || "?"} size={56} />
              </span>
            </span>
            <Link
              to="/stories/new"
              onClick={(e) => e.stopPropagation()}
              className="absolute bottom-0 right-0 flex h-5 w-5 items-center justify-center rounded-full border-2 border-white bg-sky-500 text-xs font-bold text-white"
              aria-label="Add story"
            >
              +
            </Link>
          </button>
          <span className="w-16 truncate text-center text-xs text-neutral-600">
            Your story
          </span>
        </div>

        {otherGroups.map((group) => {
          const orderedIndex = orderedGroups.indexOf(group);
          return (
            <div
              key={group.user_id}
              className="flex w-16 shrink-0 flex-col items-center gap-1"
            >
              <button
                type="button"
                onClick={() => setOpenIndex(orderedIndex)}
                className={`flex rounded-full p-[2px] ${
                  hasUnviewed(group)
                    ? "bg-gradient-to-tr from-amber-400 via-pink-500 to-purple-600"
                    : "bg-neutral-200"
                }`}
              >
                <span className="rounded-full border-2 border-white">
                  <Avatar name={group.username} size={56} />
                </span>
              </button>
              <span className="w-16 truncate text-center text-xs text-neutral-600">
                {group.username}
              </span>
            </div>
          );
        })}
      </div>

      {openIndex !== null && orderedGroups[openIndex] && (
        <StoryViewer
          groups={orderedGroups}
          startIndex={openIndex}
          currentUserId={user?.id}
          onClose={() => setOpenIndex(null)}
          onViewed={markViewed}
          onDeleted={() => {
            setOpenIndex(null);
            refresh();
          }}
        />
      )}
    </div>
  );
}
