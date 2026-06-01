export default function PlaceholderPage({ title }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-neutral-300 bg-white py-20 text-center">
      <h2 className="text-lg font-semibold text-neutral-800">{title}</h2>
      <p className="mt-2 max-w-sm text-sm text-neutral-500">
        This section is coming in a later build session.
      </p>
    </div>
  );
}
