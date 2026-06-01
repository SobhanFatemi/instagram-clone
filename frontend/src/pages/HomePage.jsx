import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getFeed } from "../api/posts";
import PostCard from "../components/PostCard";
import Spinner from "../components/Spinner";
import StoriesTray from "../components/StoriesTray";

export default function HomePage() {
  const [posts, setPosts] = useState([]);
  const [page, setPage] = useState(1);
  const [next, setNext] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await getFeed(1);
        setPosts(data.results);
        setNext(data.next);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function loadMore() {
    if (loadingMore || !next) return;
    setLoadingMore(true);
    try {
      const data = await getFeed(page + 1);
      setPosts((current) => [...current, ...data.results]);
      setNext(data.next);
      setPage((p) => p + 1);
    } finally {
      setLoadingMore(false);
    }
  }

  function handlePostChange(updated) {
    setPosts((current) =>
      current.map((p) => (p.id === updated.id ? updated : p))
    );
  }

  function handlePostDeleted(id) {
    setPosts((current) => current.filter((p) => p.id !== id));
  }

  return (
    <div className="space-y-6">
      <StoriesTray />

      {loading ? (
        <Spinner label="Loading your feed..." />
      ) : posts.length === 0 ? (
        <div className="rounded-xl border border-neutral-200 bg-white py-16 text-center">
          <p className="text-sm font-semibold text-neutral-800">
            Your feed is empty
          </p>
          <p className="mt-1 text-sm text-neutral-500">
            Follow people or share your first post.
          </p>
          <Link
            to="/create"
            className="mt-4 inline-block rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-600"
          >
            Create post
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {posts.map((post) => (
            <PostCard
              key={post.id}
              post={post}
              onChange={handlePostChange}
              onDeleted={handlePostDeleted}
            />
          ))}

          {next && (
            <div className="flex justify-center">
              <button
                type="button"
                onClick={loadMore}
                disabled={loadingMore}
                className="rounded-lg border border-neutral-300 px-5 py-2 text-sm font-semibold text-neutral-700 transition hover:bg-neutral-100 disabled:opacity-60"
              >
                {loadingMore ? "Loading..." : "Load more"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
