import { Block } from "@/components/Skeleton";

export default function Loading() {
  return (
    <div>
      <div className="mb-6 space-y-2">
        <Block className="h-7 w-40" />
        <Block className="h-4 w-56" />
      </div>
      <Block className="mb-4 h-14 w-full" />
      <div className="card space-y-2 p-3">
        {Array.from({ length: 10 }).map((_, i) => (
          <Block key={i} className="h-11 w-full" />
        ))}
      </div>
    </div>
  );
}
