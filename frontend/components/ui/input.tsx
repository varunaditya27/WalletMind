"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, label, error, icon, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-foreground mb-2">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-secondary">
              {icon}
            </div>
          )}
          <input
            type={type}
            className={cn(
              "flex w-full rounded-xl px-4 py-3 text-base transition-all duration-200",
              "bg-white/5 text-foreground placeholder:text-secondary/50",
              "border border-white/10 focus:border-indigo-500/50",
              "shadow-inner focus:shadow-lg focus:ring-2 focus:ring-indigo-500/20",
              "disabled:cursor-not-allowed disabled:opacity-50",
              icon && "pl-12",
              error && "border-red-500/50 focus:border-red-500 focus:ring-red-500/20",
              className
            )}
            ref={ref}
            {...props}
          />
        </div>
        {error && (
          <p className="mt-1.5 text-sm text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
