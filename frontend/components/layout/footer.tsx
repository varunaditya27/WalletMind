"use client";

import Link from "next/link";
import { Github, Twitter, Globe } from "lucide-react";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-auto border-t border-white/10 glass">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* About */}
          <div>
            <h3 className="text-lg font-bold mb-3 gradient-text">WalletMind</h3>
            <p className="text-sm text-secondary leading-relaxed">
              Next-generation blockchain platform merging AI autonomy with decentralized finance.
            </p>
          </div>

          {/* Links */}
          <div>
            <h3 className="text-lg font-bold mb-3">Resources</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/docs" className="text-secondary hover:text-foreground transition-colors">
                  Documentation
                </Link>
              </li>
              <li>
                <Link href="/api" className="text-secondary hover:text-foreground transition-colors">
                  API Reference
                </Link>
              </li>
              <li>
                <Link href="/about" className="text-secondary hover:text-foreground transition-colors">
                  About Us
                </Link>
              </li>
            </ul>
          </div>

          {/* Social */}
          <div>
            <h3 className="text-lg font-bold mb-3">Connect</h3>
            <div className="flex gap-3">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
              >
                <Github className="h-5 w-5" />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
              >
                <Twitter className="h-5 w-5" />
              </a>
              <a
                href="https://example.com"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
              >
                <Globe className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-white/10 text-center text-sm text-secondary">
          © {currentYear} WalletMind. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
