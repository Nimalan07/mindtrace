"use client";

import React, { useState, useMemo } from "react";
import { Search, BookOpen, CheckCircle, Clock, AlertTriangle } from "lucide-react";
import { ConceptMasteryView, MasteryStatus } from "@/types/analytics.types";
import { formatProbability, cn } from "@/lib/utils";

interface ConceptMasteryBreakdownProps {
  concepts: ConceptMasteryView[];
}

export function ConceptMasteryBreakdown({ concepts }: ConceptMasteryBreakdownProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedTopic, setSelectedTopic] = useState<string>("all");

  const topics = useMemo(() => {
    const set = new Set<string>();
    concepts.forEach((c) => {
      if (c.topic) set.add(c.topic);
    });
    return Array.from(set).sort();
  }, [concepts]);

  const filteredConcepts = useMemo(() => {
    return concepts.filter((c) => {
      const matchesSearch =
        c.concept_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.concept_id.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus =
        statusFilter === "all" || c.status === statusFilter;
      const matchesTopic =
        selectedTopic === "all" || c.topic === selectedTopic;
      return matchesSearch && matchesStatus && matchesTopic;
    });
  }, [concepts, searchQuery, statusFilter, selectedTopic]);

  const getStatusBadge = (status: MasteryStatus) => {
    switch (status) {
      case "mastered":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200">
            <CheckCircle className="w-3 h-3 text-teal-600" />
            <span>Mastered</span>
          </span>
        );
      case "practicing":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <Clock className="w-3 h-3 text-blue-600" />
            <span>Practicing</span>
          </span>
        );
      case "needs_support":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-3 h-3 text-amber-600" />
            <span>Needs Support</span>
          </span>
        );
    }
  };

  const getProgressBarColor = (status: MasteryStatus) => {
    switch (status) {
      case "mastered":
        return "bg-teal-500";
      case "practicing":
        return "bg-blue-500";
      case "needs_support":
        return "bg-amber-500";
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-5">
      {/* Header and Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-teal-600" />
            <span>Prerequisite Concept Mastery Breakdown</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time Bayesian posterior mastery across all {concepts.length} Physics curriculum concepts
          </p>
        </div>

        {/* Search & Topic Filters */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search concepts..."
              className="pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-teal-500 w-48 text-slate-800"
            />
          </div>

          {topics.length > 0 && (
            <select
              value={selectedTopic}
              onChange={(e) => setSelectedTopic(e.target.value)}
              className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-teal-500 text-slate-700"
            >
              <option value="all">All Topics</option>
              {topics.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          )}

          <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50">
            {["all", "mastered", "practicing", "needs_support"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={cn(
                  "px-2.5 py-1 text-xs font-medium rounded-md capitalize transition-all",
                  statusFilter === st
                    ? "bg-white text-slate-900 shadow-2xs font-semibold"
                    : "text-slate-500 hover:text-slate-800"
                )}
              >
                {st.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Concept Items Table / List */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-100 text-[11px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-50/50">
              <th className="py-3 px-4">Concept</th>
              <th className="py-3 px-3">Topic</th>
              <th className="py-3 px-4 w-56">Mastery Probability (BKT)</th>
              <th className="py-3 px-3 text-center">Status</th>
              <th className="py-3 px-4 text-right">Practice Opportunities</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
            {filteredConcepts.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-400">
                  No concepts match the current filter criteria.
                </td>
              </tr>
            ) : (
              filteredConcepts.map((c) => {
                const percentage = Math.min(100, Math.max(0, c.mastery_probability * 100));
                return (
                  <tr key={c.concept_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 font-medium text-slate-900">
                      <div>
                        <span className="font-semibold">{c.concept_name}</span>
                        <span className="text-[10px] text-slate-400 block font-mono">
                          {c.concept_id}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-slate-500">
                      <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-[11px]">
                        {c.topic || "Core"}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="space-y-1">
                        <div className="flex justify-between text-[11px] font-mono">
                          <span className="font-semibold text-slate-800">
                            {formatProbability(c.mastery_probability)}
                          </span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                          <div
                            className={cn(
                              "h-2 rounded-full transition-all duration-300",
                              getProgressBarColor(c.status)
                            )}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-center">
                      {getStatusBadge(c.status)}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-600 font-mono">
                      <span>{c.opportunities} attempts</span>
                      <span className="text-slate-400 text-[11px] block">
                        {c.correct_count} correct
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
