"use client";

import React, { ReactNode } from "react";
import { StudentProvider } from "@/context/StudentContext";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <StudentProvider>
      <div className="flex h-screen w-screen overflow-hidden bg-[#F8FAFC]">
        <Sidebar />
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
          <Navbar />
          <main className="flex-1 overflow-y-auto p-6 md:p-8">
            <div className="max-w-7xl mx-auto space-y-6">{children}</div>
          </main>
        </div>
      </div>
    </StudentProvider>
  );
}
