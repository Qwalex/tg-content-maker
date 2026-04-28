import "./globals.css";
import Link from "next/link";
import type { ReactNode } from "react";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="mx-auto max-w-6xl p-6">
        <nav className="mb-6 flex gap-4 border-b border-slate-800 pb-3 text-sm">
          <Link href="/">Dashboard</Link>
          <Link href="/sessions">Sessions</Link>
          <Link href="/copiers">Copiers</Link>
          <Link href="/settings">Settings</Link>
          <Link href="/logs">Logs</Link>
        </nav>
        {children}
      </body>
    </html>
  );
}
