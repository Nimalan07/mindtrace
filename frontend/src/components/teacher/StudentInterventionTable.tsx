"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { User, ArrowUpRight, AlertOctagon } from "lucide-react";
import { StudentAtRiskView } from "@/types/analytics.types";
import { useStudent } from "@/context/StudentContext";
import { formatPercent } from "@/lib/utils";

interface StudentInterventionTableProps {
  studentsAtRisk: StudentAtRiskView[];
}

export function StudentInterventionTable({
  studentsAtRisk,
}: StudentInterventionTableProps) {
  const router = useRouter();
  const { setCurrentStudentId } = useStudent();

  const handleNavigateToStudent = (studentId: string) => {
    setCurrentStudentId(studentId);
    router.push("/student/dashboard");
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <AlertOctagon className="w-5 h-5 text-rose-600" />
            <span>Students Requiring Targeted Instructional Remediation</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Learners whose BKT deficit or diagnosed reasoning traps warrant educator intervention
          </p>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-rose-50 text-rose-800 border border-rose-200">
          {studentsAtRisk.length} Flagged
        </span>
      </div>

      {studentsAtRisk.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-400 bg-slate-50 rounded-xl border border-slate-100">
          No students currently meet the at-risk criteria in this cohort.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 text-[11px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-50/50">
                <th className="py-3 px-4">Student Profile</th>
                <th className="py-3 px-3">Proficiency</th>
                <th className="py-3 px-3">Primary Deficit</th>
                <th className="py-3 px-3">Active Misconceptions</th>
                <th className="py-3 px-4">Recommended Pedagogical Action</th>
                <th className="py-3 px-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
              {studentsAtRisk.map((s) => (
                <tr key={s.student_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-slate-900">
                    <button
                      onClick={() => handleNavigateToStudent(s.student_id)}
                      className="text-teal-700 hover:text-teal-900 hover:underline flex items-center gap-1.5"
                    >
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      <span>{s.student_id}</span>
                    </button>
                  </td>
                  <td className="py-3 px-3 font-mono font-semibold text-rose-700">
                    {formatPercent(s.overall_proficiency)}
                  </td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-mono text-[11px] font-semibold">
                      {s.primary_deficit_concept}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    {s.active_misconceptions.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {s.active_misconceptions.map((m) => (
                          <span
                            key={m}
                            className="px-1.5 py-0.2 rounded bg-rose-100 text-rose-800 font-mono text-[10px] font-bold"
                          >
                            {m}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-slate-400 text-[11px] italic">None verified</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-slate-800 font-medium max-w-xs truncate">
                    {s.recommended_intervention}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => handleNavigateToStudent(s.student_id)}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-teal-600 hover:text-teal-800 px-2.5 py-1 rounded-md bg-teal-50 hover:bg-teal-100 transition-colors"
                    >
                      <span>View</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
