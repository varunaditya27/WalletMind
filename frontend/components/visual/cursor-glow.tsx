'use client';

import { motion, useMotionValue, useSpring } from "framer-motion";
import { useEffect } from "react";

const springConfig = { damping: 90, stiffness: 550, mass: 0.8 };

export function CursorGlow() {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const springX = useSpring(mouseX, springConfig);
  const springY = useSpring(mouseY, springConfig);

  useEffect(() => {
    const handlePointerMove = (event: PointerEvent) => {
      mouseX.set(event.clientX - window.innerWidth / 2);
      mouseY.set(event.clientY - window.innerHeight / 2);
    };
    window.addEventListener("pointermove", handlePointerMove, { passive: true });
    return () => window.removeEventListener("pointermove", handlePointerMove);
  }, [mouseX, mouseY]);

  return (
    <motion.div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-40 flex items-center justify-center"
      style={{ transform: "translate3d(0,0,0)" }}
    >
      <motion.div
        className="h-56 w-56 rounded-full bg-accent/20 blur-3xl"
        style={{ x: springX, y: springY }}
      />
    </motion.div>
  );
}
