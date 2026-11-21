import type { Metadata } from "next";
import { AppShell } from "@/components/layout/AppShell";
import "./globals.css";

export const metadata: Metadata = {
  title: "MINDTRACE — Adaptive Reasoning Diagnosis & Learning",
  description:
    "AI-powered reasoning diagnosis, Bayesian misconception verification, and adaptive BKT mastery progression.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full antialiased font-sans bg-[#F8FAFC] text-[#0F172A]">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
