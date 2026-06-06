// Shimmering placeholder block used by route-level loading.tsx fallbacks.
export function Block({ className = "" }: { className?: string }) {
  return (
    <div
      className={`relative overflow-hidden rounded-xl bg-white/[0.04] sheen ${className}`}
    />
  );
}
