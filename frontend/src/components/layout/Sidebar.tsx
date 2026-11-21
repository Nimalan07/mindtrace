"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BrainCircuit,
  GraduationCap,
  Users,
  ChevronLeft,
  ChevronRight,
  Layers,
} from "lucide-react";
import { analyticsService } from "@/services/analytics.service";
import { HealthResponse } from "@/types/analytics.types";
import { cn } from "@/lib/utils";

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  phaseTag?: string;
  isAvailable: boolean;
}

const NAV_ITEMS: NavItem[] = [
  {
    title: "Student Dashboard",
    href: "/student/dashboard",
    icon: LayoutDashboard,
    isAvailable: true,
  },
  {
    title: "Diagnostic Assessment",
    href: "/student/assessment",
    icon: BrainCircuit,
    phaseTag: "Phase C",
    isAvailable: false,
  },
  {
    title: "Adaptive Learning",
    href: "/student/learning",
    icon: GraduationCap,
    phaseTag: "Phase D",
    isAvailable: false,
  },
  {
    title: "Educator Dashboard",
    href: "/teacher/dashboard",
    icon: Users,
    phaseTag: "Phase E",
    isAvailable: false,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchHealth = async () => {
      try {
        const data = await analyticsService.getHealth();
        if (isMounted) {
          setHealth(data);
          setHealthError(false);
        }
      } catch {
        if (isMounted) {
          setHealthError(true);
        }
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <aside
      className={cn(
        "relative flex flex-col bg-[#14213D] text-white transition-all duration-300 ease-in-out border-r border-slate-800 shrink-0 select-none z-30",
        collapsed ? "w-20" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/80">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-teal-500 flex items-center justify-center shrink-0 shadow-lg shadow-teal-500/20">
            <Layers className="w-6 h-6 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col min-w-0">
              <span className="font-bold text-lg tracking-tight text-white truncate">
                MINDTRACE
              </span>
              <span className="text-[10px] uppercase tracking-wider text-teal-400 font-medium">
                Reasoning Diagnosis
              </span>
            </div>
          )}
        </div>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors ml-auto"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          {!collapsed && "Modules"}
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 relative",
                isActive
                  ? "bg-teal-500/20 text-teal-300 shadow-sm border border-teal-500/30"
                  : "text-slate-300 hover:bg-slate-800/70 hover:text-white"
              )}
              title={collapsed ? `${item.title}${item.phaseTag ? ` (${item.phaseTag})` : ""}` : undefined}
            >
              <Icon
                className={cn(
                  "w-5 h-5 shrink-0 transition-colors",
                  isActive ? "text-teal-400" : "text-slate-400 group-hover:text-white"
                )}
              />
              {!collapsed && (
                <div className="flex items-center justify-between w-full min-w-0">
                  <span className="truncate">{item.title}</span>
                  {item.phaseTag && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                      {item.phaseTag}
                    </span>
                  )}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* System Engine Status Footer */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-900/40">
        {!collapsed ? (
          <div className="p-2.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs">
            <div className="flex items-center gap-2 mb-1">
              <span
                className={cn(
                  "w-2 h-2 rounded-full animate-pulse",
                  healthError ? "bg-amber-400" : health ? "bg-emerald-400" : "bg-slate-400"
                )}
              />
              <span className="font-semibold text-slate-200">
                {healthError ? "Connecting..." : health ? "Engine Ready" : "Initializing"}
              </span>
            </div>
            {health && (
              <p className="text-[11px] text-slate-400 leading-tight">
                {health.registered_concepts} concepts • {health.registered_misconceptions} misconceptions
              </p>
            )}
            {healthError && (
              <p className="text-[11px] text-amber-300/80 leading-tight">
                Backend on :8000
              </p>
            )}
          </div>
        ) : (
          <div className="flex justify-center" title="Engine Status">
            <span
              className={cn(
                "w-2.5 h-2.5 rounded-full",
                healthError ? "bg-amber-400" : health ? "bg-emerald-400" : "bg-slate-400"
              )}
            />
          </div>
        )}
      </div>
    </aside>
  );
}
