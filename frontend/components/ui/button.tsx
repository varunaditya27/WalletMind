"use client";

import * as React from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface ButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onDrag' | 'onDragStart' | 'onDragEnd'> {
  variant?: "primary" | "secondary" | "ghost" | "outline" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  icon?: React.ReactNode;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", loading, icon, children, disabled, ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center gap-2 font-semibold tracking-wide transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed uppercase text-sm";
    
    const variants = {
      primary: "bg-gradient-to-r from-indigo-600 to-indigo-700 text-white hover:from-indigo-500 hover:to-indigo-600 focus:ring-indigo-500 shadow-lg hover:shadow-xl glow-hover",
      secondary: "glass text-foreground hover:bg-white/10 focus:ring-secondary shadow-md hover:shadow-lg",
      ghost: "text-foreground hover:bg-white/5 focus:ring-secondary",
      outline: "border-2 border-indigo-500/50 text-indigo-400 hover:bg-indigo-500/10 focus:ring-indigo-500",
      danger: "bg-gradient-to-r from-red-600 to-red-700 text-white hover:from-red-500 hover:to-red-600 focus:ring-red-500 shadow-lg hover:shadow-xl",
    };
    
    const sizes = {
      sm: "px-4 py-2 rounded-lg text-xs",
      md: "px-6 py-3 rounded-xl text-sm",
      lg: "px-8 py-4 rounded-2xl text-base",
    };

    const MotionButton = motion.button;

    return (
      <MotionButton
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || loading}
        whileHover={disabled || loading ? {} : { scale: 1.02 }}
        whileTap={disabled || loading ? {} : { scale: 0.98 }}
        {...(props as any)}
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Processing...</span>
          </>
        ) : (
          <>
            {icon && <span className="inline-flex">{icon}</span>}
            {children}
          </>
        )}
      </MotionButton>
    );
  }
);

Button.displayName = "Button";

export { Button };
