import { Block } from "@/components/Skeleton";

// Shown automatically during navigation while a page's server data loads.
export default function Loading() {
  return (
    <div>
      <div className="mb-6 space-y-2">
        <Block className="h-7 w-56" />
        <Block className="h-4 w-80" />
      </div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Block key={i} className="h-[88px]" />
        ))}
      </div>
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Block key={i} className="h-56" />
        ))}
      </div>
    </div>
  );
}
