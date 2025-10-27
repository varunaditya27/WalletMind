"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "primary" | "success" | "warning" | "error" | "neutral";
  size?: "sm" | "md" | "lg";
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = "neutral", size = "md", ...props }, ref) => {
    const variants = {
      primary: "bg-indigo-500/20 text-indigo-300 border-indigo-500/30",
      success: "bg-green-500/20 text-green-300 border-green-500/30",
      warning: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
      error: "bg-red-500/20 text-red-300 border-red-500/30",
      neutral: "bg-slate-500/20 text-slate-300 border-slate-500/30",
    };

    const sizes = {
      sm: "px-2 py-0.5 text-xs",
      md: "px-3 py-1 text-sm",
      lg: "px-4 py-1.5 text-base",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "inline-flex items-center rounded-full font-medium border",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);

Badge.displayName = "Badge";

export { Badge };
