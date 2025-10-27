"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {}

function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-xl bg-white/5 shimmer",
        className
      )}
      {...props}
    />
  );
}

export { Skeleton };
