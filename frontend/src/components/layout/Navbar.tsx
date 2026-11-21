"use client";

import React, { useState } from "react";
import { usePathname } from "next/navigation";
import { UserCheck, Sparkles, ChevronDown, Check, ArrowRight } from "lucide-react";
import { useStudent } from "@/context/StudentContext";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();
  const { currentStudentId, setCurrentStudentId, availableStudents } = useStudent();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [customInput, setCustomInput] = useState("");
  const [showCustomInput, setShowCustomInput] = useState(false);

  const getPageTitle = () => {
    if (pathname.includes("/student/dashboard")) return "Student Learning Intelligence Dashboard";
    if (pathname.includes("/student/assessment")) return "Diagnostic Assessment";
    if (pathname.includes("/student/learning")) return "Adaptive Learning & Interventions";
    if (pathname.includes("/teacher/dashboard")) return "Educator Diagnostic Dashboard";
    return "MINDTRACE Portal";
  };

  const handleSelectStudent = (id: string) => {
    setCurrentStudentId(id);
    setDropdownOpen(false);
    setShowCustomInput(false);
  };

  const [inputError, setInputError] = useState<string | null>(null);

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = customInput.trim();
    if (!trimmed) return;
    if (!/^[a-zA-Z0-9_-]{1,64}$/.test(trimmed)) {
      setInputError("ID must be 1-64 alphanumeric chars, underscores, or hyphens.");
      return;
    }
    setCurrentStudentId(trimmed);
    setDropdownOpen(false);
    setShowCustomInput(false);
    setCustomInput("");
    setInputError(null);
  };

  const activeStudentInfo = availableStudents.find((s) => s.id === currentStudentId) || {
    id: currentStudentId,
    label: currentStudentId,
    badge: "Custom Student",
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20 shadow-xs">
      {/* Breadcrumb / Title */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
          MINDTRACE
        </span>
        <span className="text-slate-400">/</span>
        <h1 className="text-base font-semibold text-slate-800">{getPageTitle()}</h1>
      </div>

      {/* Right side controls: Live Student Switcher */}
      <div className="flex items-center gap-4">
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-3 px-3.5 py-1.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 hover:border-slate-300 transition-all text-left shadow-2xs"
            aria-label="Select student account"
            aria-expanded={dropdownOpen}
            aria-haspopup="dialog"
          >
            <div className="w-7 h-7 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
              <UserCheck className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-slate-900 leading-tight">
                  {activeStudentInfo.label}
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded-full font-medium bg-teal-100 text-teal-800 border border-teal-200">
                  {activeStudentInfo.badge}
                </span>
              </div>
              <span className="text-[10px] text-slate-600 font-mono">
                ID: {currentStudentId}
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-600 ml-1" />
          </button>

          {/* Student Dropdown Menu */}
          {dropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setDropdownOpen(false)}
              />
              <div className="absolute right-0 mt-2 w-72 bg-white rounded-xl shadow-xl border border-slate-200 p-2 z-20 animate-in fade-in slide-in-from-top-1 duration-150">
                <div className="px-2 py-1.5 border-b border-slate-100 text-[11px] font-semibold uppercase tracking-wider text-slate-600">
                  Select Active Student Profile
                </div>
                <div className="py-1 space-y-1">
                  {availableStudents.map((student) => {
                    const isSelected = student.id === currentStudentId;
                    return (
                      <button
                        key={student.id}
                        onClick={() => handleSelectStudent(student.id)}
                        className={cn(
                          "w-full text-left px-2.5 py-2 rounded-lg text-xs flex items-center justify-between transition-colors",
                          isSelected
                            ? "bg-teal-50 text-teal-900 font-medium"
                            : "hover:bg-slate-50 text-slate-700"
                        )}
                      >
                        <div className="flex flex-col">
                          <span className="font-semibold">{student.label}</span>
                          <span className="text-[10px] text-slate-600 font-mono">{student.id}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                            {student.badge}
                          </span>
                          {isSelected && <Check className="w-3.5 h-3.5 text-teal-600" />}
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Custom Student ID Option */}
                <div className="pt-2 border-t border-slate-100">
                  {!showCustomInput ? (
                    <button
                      onClick={() => setShowCustomInput(true)}
                      className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                      <span>Switch to custom student ID...</span>
                    </button>
                  ) : (
                    <form onSubmit={handleCustomSubmit} className="p-1 space-y-2">
                      <input
                        type="text"
                        value={customInput}
                        onChange={(e) => {
                          setCustomInput(e.target.value);
                          if (inputError) setInputError(null);
                        }}
                        placeholder="Enter student ID..."
                        className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-teal-500 font-mono"
                        autoFocus
                        aria-label="Custom Student ID input"
                      />
                      {inputError && (
                        <p className="text-[10px] text-rose-600 font-medium leading-tight">{inputError}</p>
                      )}
                      <div className="flex gap-2 justify-end">
                        <button
                          type="button"
                          onClick={() => setShowCustomInput(false)}
                          className="px-2 py-1 text-xs text-slate-500 hover:text-slate-700"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          className="px-2.5 py-1 text-xs bg-teal-600 text-white rounded-md hover:bg-teal-700 flex items-center gap-1 font-medium"
                        >
                          <span>Load</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
