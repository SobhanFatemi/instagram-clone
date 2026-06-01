import { useEffect, useState } from "react";

import { getExplore } from "../api/feed";
import PostGrid from "../components/PostGrid";
import Spinner from "../components/Spinner";

export default function ExplorePage() {
  const [posts, setPosts] = useState([]);
  const [page, setPage] = useState(1);
  const [next, setNext] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await getExplore(1);
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
      const data = await getExplore(page + 1);
      setPosts((current) => [...current, ...data.results]);
      setNext(data.next);
      setPage((p) => p + 1);
    } finally {
      setLoadingMore(false);
    }
  }

  if (loading) return <Spinner label="Loading explore..." />;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-neutral-900">Explore</h2>

      <PostGrid
        posts={posts}
        emptyText="Nothing to explore yet. Follow a few people and check back."
      />

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
