"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LandingPage } from "@/components/pages/landing";
import { authService } from "@/lib/services/auth-service";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // If user is already authenticated and onboarding complete, redirect to dashboard
    if (authService.isAuthenticated()) {
      const user = authService.getUser();
      if (user?.onboarding_complete) {
        router.push("/dashboard");
      }
    }
  }, [router]);

  return <LandingPage />;
}
