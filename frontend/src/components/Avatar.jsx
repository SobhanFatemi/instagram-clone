import { mediaUrl } from "../lib/media";

export default function Avatar({ src, name, size = 40, className = "" }) {
  const url = mediaUrl(src);
  const initial = (name || "?").trim().slice(0, 1).toUpperCase();
  const dimensions = { width: size, height: size };

  if (url) {
    return (
      <img
        src={url}
        alt={name || "avatar"}
        style={dimensions}
        className={`shrink-0 rounded-full object-cover ${className}`}
      />
    );
  }

  return (
    <div
      style={dimensions}
      className={`flex shrink-0 items-center justify-center rounded-full bg-gradient-to-tr from-amber-300 via-pink-500 to-purple-600 font-semibold text-white ${className}`}
    >
      <span style={{ fontSize: size * 0.4 }}>{initial}</span>
    </div>
  );
}
