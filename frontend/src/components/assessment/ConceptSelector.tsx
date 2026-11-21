"use client";

import React, { useState, useMemo } from "react";
import { Search, Compass, GitFork, ArrowRight } from "lucide-react";
import { ConceptDetailView } from "@/types/diagnosis.types";
import { cn } from "@/lib/utils";

interface ConceptSelectorProps {
  concepts: ConceptDetailView[];
  selectedConceptId: string | null;
  onSelectConcept: (concept: ConceptDetailView) => void;
  loading?: boolean;
}

export function ConceptSelector({
  concepts,
  selectedConceptId,
  onSelectConcept,
  loading,
}: ConceptSelectorProps) {
  const [search, setSearch] = useState("");
  const [selectedTopic, setSelectedTopic] = useState<string>("all");

  const topics = useMemo(() => {
    const set = new Set<string>();
    concepts.forEach((c) => {
      if (c.topic) set.add(c.topic);
    });
    return Array.from(set).sort();
  }, [concepts]);

  const filtered = useMemo(() => {
    return concepts.filter((c) => {
      const matchSearch =
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.description.toLowerCase().includes(search.toLowerCase()) ||
        c.id.toLowerCase().includes(search.toLowerCase());
      const matchTopic = selectedTopic === "all" || c.topic === selectedTopic;
      return matchSearch && matchTopic;
    });
  }, [concepts, search, selectedTopic]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-44 bg-slate-200 rounded-2xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Intro banner */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-xs font-semibold">
            <Compass className="w-3.5 h-3.5 text-teal-600" />
            <span>Step A: Target Concept Selection</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Select a Physics Concept to Diagnose
          </h2>
          <p className="text-xs text-slate-500 max-w-xl">
            Choose a target concept from the verified 23-node prerequisite concept graph. The system will present an open-ended reasoning problem to diagnose potential misconceptions.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search concepts..."
              aria-label="Search concepts"
              className="pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-teal-500 w-44 text-slate-800"
            />
          </div>

          <select
            value={selectedTopic}
            onChange={(e) => setSelectedTopic(e.target.value)}
            aria-label="Filter concepts by topic"
            className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-teal-500 text-slate-700"
          >
            <option value="all">All Topics ({concepts.length})</option>
            {topics.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Concept Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((concept) => {
          const isSelected = selectedConceptId === concept.id;
          return (
            <div
              key={concept.id}
              onClick={() => onSelectConcept(concept)}
              className={cn(
                "group text-left p-5 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col justify-between relative shadow-xs hover:shadow-md",
                isSelected
                  ? "bg-teal-50/50 border-teal-500 ring-2 ring-teal-500/20 shadow-teal-500/10"
                  : "bg-white border-slate-200/80 hover:border-teal-400 hover:bg-slate-50/60"
              )}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                    {concept.topic || "Core"}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">
                    {concept.id}
                  </span>
                </div>

                <h3 className="text-base font-bold text-slate-900 group-hover:text-teal-700 transition-colors">
                  {concept.name}
                </h3>

                <p className="mt-2 text-xs text-slate-600 line-clamp-3 leading-relaxed">
                  {concept.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                  <GitFork className="w-3.5 h-3.5 text-slate-400" />
                  <span>
                    {concept.prerequisites.length > 0
                      ? `${concept.prerequisites.length} Prereq${concept.prerequisites.length > 1 ? "s" : ""}`
                      : "Foundational"}
                  </span>
                </div>

                <div
                  className={cn(
                    "inline-flex items-center gap-1 text-xs font-semibold transition-colors",
                    isSelected ? "text-teal-700" : "text-slate-400 group-hover:text-teal-600"
                  )}
                >
                  <span>{isSelected ? "Selected" : "Diagnose"}</span>
                  <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
