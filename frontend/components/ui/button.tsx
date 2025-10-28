import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "group/button relative inline-flex items-center justify-center gap-2 overflow-hidden rounded-xl border border-white/5 px-4 py-2 text-sm font-semibold tracking-wide text-foreground transition-all duration-300 ease-gentle hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/70 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-55",
  {
    variants: {
      variant: {
        primary:
          "bg-accent text-background shadow-accent-ring before:absolute before:inset-0 before:-z-10 before:bg-linear-to-r before:from-accent before:via-accent/80 before:to-accent/60 before:opacity-0 before:transition-opacity before:duration-400 group-hover/button:before:opacity-100",
        secondary:
          "bg-surface/80 text-foreground hover:bg-surface/95 hover:shadow-gold-ring",
        ghost:
          "bg-transparent text-foreground hover:bg-white/5 active:bg-white/10",
        outline:
          "border-accent/40 bg-transparent text-accent hover:bg-accent/10",
        glass:
          "bg-white/5 text-foreground backdrop-blur-18 hover:bg-white/10",
      },
      size: {
        sm: "h-9 px-3 text-xs",
        md: "h-11 px-4 text-sm",
        lg: "h-12 px-6 text-base",
        pill: "h-12 px-8 text-base rounded-full",
        icon: "h-10 w-10 p-0",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";

    return (
      <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
    );
  }
);

Button.displayName = "Button";

export { Button, buttonVariants };
