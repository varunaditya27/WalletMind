"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/layout/app-shell";
import { authService } from "@/lib/services/auth-service";

export default function AppLayout({ children }: { children: ReactNode }) {
  const router = useRouter();

  useEffect(() => {
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
  }, [router]);

  // Don't render app shell until auth check is complete
  if (!authService.isAuthenticated()) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
        <div className="text-white">Checking authentication...</div>
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}
