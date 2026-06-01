import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getSavedPosts } from "../api/posts";
import PostGrid from "../components/PostGrid";
import Spinner from "../components/Spinner";

export default function SavedPostsPage() {
  const [posts, setPosts] = useState([]);
  const [page, setPage] = useState(1);
  const [next, setNext] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await getSavedPosts(1);
        setPosts(data.results.map((item) => item.post));
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
      const data = await getSavedPosts(page + 1);
      setPosts((current) => [...current, ...data.results.map((item) => item.post)]);
      setNext(data.next);
      setPage((p) => p + 1);
    } finally {
      setLoadingMore(false);
    }
  }

  if (loading) return <Spinner label="Loading saved posts..." />;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link
          to="/profile"
          className="text-sm text-neutral-500 transition hover:text-neutral-800"
        >
          &larr; Back
        </Link>
        <h2 className="text-xl font-semibold text-neutral-900">Saved</h2>
      </div>

      <PostGrid posts={posts} emptyText="You haven't saved any posts yet." />

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
  );
}
