export default function Spinner({ label = "Loading..." }) {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-3 py-16">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-neutral-300 border-t-neutral-800" />
      <p className="text-sm text-neutral-500">{label}</p>
    </div>
  );
}
