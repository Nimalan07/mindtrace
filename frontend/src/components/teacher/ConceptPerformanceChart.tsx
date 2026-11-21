"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { BarChart3 } from "lucide-react";
import { ConceptHeatmapView } from "@/types/analytics.types";

interface ConceptPerformanceChartProps {
  heatmaps: ConceptHeatmapView[];
}

export function ConceptPerformanceChart({ heatmaps }: ConceptPerformanceChartProps) {
  // Sort concepts by average mastery ascending to show weakest concepts first
  const sorted = [...heatmaps]
    .sort((a, b) => a.average_mastery - b.average_mastery)
    .slice(0, 10);

  const chartData = sorted.map((c) => ({
    name: c.concept_name.length > 16 ? `${c.concept_name.slice(0, 14)}...` : c.concept_name,
    fullName: c.concept_name,
    mastery: Math.round(c.average_mastery * 100),
    struggling: c.struggling_students_count,
    mastered: c.mastered_students_count,
  }));

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-teal-600" />
            <span>Classroom Concept Mastery Distribution (Top Focus Areas)</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Average BKT posterior mastery across concepts ranked by pedagogical intervention priority
          </p>
        </div>
      </div>

      <div className="h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis
              dataKey="name"
              angle={-25}
              textAnchor="end"
              tick={{ fontSize: 10, fill: "#64748b" }}
              interval={0}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: "#64748b" }}
              unit="%"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white p-3 rounded-xl shadow-lg text-xs space-y-1 font-sans">
                      <p className="font-bold text-teal-300">{d.fullName}</p>
                      <p>Average Mastery: <strong className="font-mono">{d.mastery}%</strong></p>
                      <p className="text-[11px] text-slate-300">
                        Struggling: {d.struggling} • Mastered: {d.mastered}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="mastery" radius={[6, 6, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.mastery < 50 ? "#F59E0B" : entry.mastery >= 75 ? "#14B8A6" : "#3B82F6"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-center gap-6 text-xs text-slate-500 pt-2 border-t border-slate-100">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
          <span>Priority Focus (&lt; 50%)</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
          <span>In Progress (50% - 74%)</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-teal-500" />
          <span>Solid (&ge; 75%)</span>
        </span>
      </div>
    </div>
  );
}
