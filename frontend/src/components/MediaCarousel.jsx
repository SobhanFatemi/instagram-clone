import { useState } from "react";

import { mediaUrl } from "../lib/media";

export default function MediaCarousel({ items }) {
  const [index, setIndex] = useState(0);

  if (!items || items.length === 0) {
    return <div className="aspect-square w-full bg-neutral-100" />;
  }

  const current = items[index];
  const many = items.length > 1;

  function go(delta) {
    setIndex((i) => (i + delta + items.length) % items.length);
  }

  return (
    <div className="relative aspect-square w-full bg-neutral-100">
      {current.media_type === "video" ? (
        <video
          src={mediaUrl(current.media)}
          controls
          className="h-full w-full bg-black object-contain"
        />
      ) : (
        <img
          src={mediaUrl(current.media)}
          alt=""
          className="h-full w-full object-cover"
        />
      )}

      {many && (
        <>
          <button
            type="button"
            onClick={() => go(-1)}
            aria-label="Previous"
            className="absolute left-2 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-black/40 text-white transition hover:bg-black/60"
          >
            ‹
          </button>
          <button
            type="button"
            onClick={() => go(1)}
            aria-label="Next"
            className="absolute right-2 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-black/40 text-white transition hover:bg-black/60"
          >
            ›
          </button>
          <div className="absolute right-2 top-2 rounded-full bg-black/60 px-2 py-0.5 text-xs font-medium text-white">
            {index + 1}/{items.length}
          </div>
          <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-1.5">
            {items.map((item, i) => (
              <span
                key={item.id}
                className={`h-1.5 w-1.5 rounded-full transition ${
                  i === index ? "bg-white" : "bg-white/50"
                }`}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
