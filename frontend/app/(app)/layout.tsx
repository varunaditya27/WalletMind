"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/layout/app-shell";
import { authService } from "@/lib/services/auth-service";

export default function AppLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  // This effect runs only on the client to prevent hydration mismatches
  // This is the standard pattern for client-only rendering in Next.js
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    // Check authentication on mount
    if (!authService.isAuthenticated()) {
      router.push("/onboarding");
      return;
    }

    // Check if onboarding is complete
    const user = authService.getUser();
    if (user && !user.onboarding_complete) {
      router.push("/onboarding");
    }
  }, [router, mounted]);

  // Show loading state during SSR and initial hydration to avoid mismatch
  if (!mounted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-linear-to-br from-gray-900 via-purple-900 to-gray-900">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  // After hydration, check auth
  if (!authService.isAuthenticated()) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-linear-to-br from-gray-900 via-purple-900 to-gray-900">
        <div className="text-white">Checking authentication...</div>
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}
