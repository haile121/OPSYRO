import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OPSYRO — Audience understanding",
  description: "See what your audience wants to understand.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
