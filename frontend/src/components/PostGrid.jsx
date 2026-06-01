import { Link } from "react-router-dom";

import { mediaUrl } from "../lib/media";

function coverFor(post) {
  const first = post.media_items && post.media_items[0];
  if (!first) return null;
  if (first.media_type === "video") {
    return first.thumbnail || first.media;
  }
  return first.media;
}

export default function PostGrid({ posts, emptyText = "No posts yet." }) {
  if (!posts.length) {
    return (
      <p className="py-16 text-center text-sm text-neutral-500">{emptyText}</p>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-1 sm:gap-2">
      {posts.map((post) => {
        const cover = coverFor(post);
        const multi = post.media_items && post.media_items.length > 1;
        const isVideo = post.media_items?.[0]?.media_type === "video";

        return (
          <Link
            key={post.id}
            to={`/p/${post.id}`}
            className="group relative aspect-square overflow-hidden bg-neutral-100"
          >
            {cover && (
              <img
                src={mediaUrl(cover)}
                alt=""
                className="h-full w-full object-cover"
              />
            )}

            {(multi || isVideo) && (
              <span className="absolute right-2 top-2 text-white drop-shadow">
                {multi ? "▦" : "▶"}
              </span>
            )}

            <div className="absolute inset-0 flex items-center justify-center gap-5 bg-black/40 text-sm font-semibold text-white opacity-0 transition group-hover:opacity-100">
              <span>♥ {post.like_count}</span>
              <span>💬 {post.comment_count}</span>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
