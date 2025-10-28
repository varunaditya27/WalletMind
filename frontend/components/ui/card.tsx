import * as React from "react";

import { cn } from "@/lib/utils";

const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "group relative overflow-hidden rounded-glass border border-white/5 bg-card backdrop-blur-18 shadow-glass transition hover:border-accent/40 hover:shadow-accent-ring",
        className
      )}
      {...props}
    />
  )
);

Card.displayName = "Card";

const CardBackground = ({ className }: { className?: string }) => (
  <span
    aria-hidden
    className={cn(
      "pointer-events-none absolute -inset-1 opacity-0 blur-2xl transition-opacity duration-400 group-hover:opacity-100",
      className
    )}
  />
);

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("relative z-10 p-6", className)} {...props} />
  )
);

CardContent.displayName = "CardContent";

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("relative z-10 p-6 pb-2", className)} {...props} />
  )
);

CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn("text-lg font-semibold text-foreground tracking-tight", className)}
      {...props}
    />
  )
);

CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn("text-sm text-muted", className)}
      {...props}
    />
  )
);

CardDescription.displayName = "CardDescription";

export {
  Card,
  CardBackground,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
};
