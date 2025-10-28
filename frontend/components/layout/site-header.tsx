import Link from "next/link";

import { Button } from "@/components/ui/button";

const navItems = [
  { href: "#features", label: "Features" },
  { href: "#agents", label: "Agents" },
  { href: "#verification", label: "Verification" },
  { href: "#cta", label: "Get Started" },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-18">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4">
        <Link href="/" className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.2em] text-muted">
          <span className="h-3 w-3 rounded-full bg-accent shadow-[0_0_24px_rgba(0,191,255,0.65)]" />
          WalletMind
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-muted lg:flex">
          {navItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="relative font-medium transition hover:text-foreground"
            >
              <span className="absolute inset-x-0 bottom-0 h-px origin-left scale-x-0 bg-linear-to-r from-accent via-gold to-accent transition-transform duration-400 hover:scale-x-100" />
              {item.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <Button variant="ghost" className="hidden text-sm text-muted hover:text-foreground sm:inline-flex" asChild>
            <Link href="/dashboard">Launch App</Link>
          </Button>
          <Button variant="primary" size="pill">
            Request Demo
          </Button>
        </div>
      </div>
    </header>
  );
}
