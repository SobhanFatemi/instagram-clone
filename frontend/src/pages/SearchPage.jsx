import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { searchHashtags, searchPosts, searchUsers } from "../api/feed";
import Avatar from "../components/Avatar";
import PostGrid from "../components/PostGrid";
import Spinner from "../components/Spinner";

const TABS = [
  { key: "users", label: "Users" },
  { key: "posts", label: "Posts" },
  { key: "tags", label: "Tags" },
];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [tab, setTab] = useState("users");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const term = query.trim();
    if (!term) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    const handle = setTimeout(async () => {
      try {
        let data;
        if (tab === "users") {
          data = await searchUsers(term);
        } else if (tab === "posts") {
          data = await searchPosts(term);
        } else {
          data = await searchHashtags(term);
        }
        setResults(data);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(handle);
  }, [query, tab]);

  function openTag(name) {
    setQuery(name);
    setTab("posts");
  }

  return (
    <div className="space-y-5">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search people, posts, and hashtags"
        autoFocus
        className="w-full rounded-lg border border-neutral-300 px-4 py-2.5 text-sm outline-none focus:border-neutral-500"
      />

      <div className="flex gap-1 border-b border-neutral-200">
        {TABS.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => setTab(item.key)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-semibold transition ${
              tab === item.key
                ? "border-neutral-900 text-neutral-900"
                : "border-transparent text-neutral-400 hover:text-neutral-600"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {!query.trim() ? (
        <p className="py-16 text-center text-sm text-neutral-500">
          Start typing to search.
        </p>
      ) : loading ? (
        <Spinner label="Searching..." />
      ) : results.length === 0 ? (
        <p className="py-16 text-center text-sm text-neutral-500">
          No {tab} found for &ldquo;{query.trim()}&rdquo;.
        </p>
      ) : tab === "users" ? (
        <ul className="space-y-1">
          {results.map((user) => (
            <li key={user.id}>
              <Link
                to={`/u/${user.username}`}
                className="flex items-center gap-3 rounded-lg px-2 py-2 transition hover:bg-neutral-100"
              >
                <Avatar src={user.avatar} name={user.display_name || user.username} />
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-neutral-900">
                    {user.username}
                  </p>
                  {user.display_name && (
                    <p className="truncate text-sm text-neutral-500">
                      {user.display_name}
                    </p>
                  )}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : tab === "posts" ? (
        <PostGrid posts={results} emptyText="No posts found." />
      ) : (
        <ul className="space-y-1">
          {results.map((tag) => (
            <li key={tag.id}>
              <button
                type="button"
                onClick={() => openTag(tag.name)}
                className="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left transition hover:bg-neutral-100"
              >
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-neutral-100 text-lg font-semibold text-neutral-500">
                  #
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-neutral-900">
                    #{tag.name}
                  </p>
                  <p className="text-sm text-neutral-500">
                    {tag.posts_count} {tag.posts_count === 1 ? "post" : "posts"}
                  </p>
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
