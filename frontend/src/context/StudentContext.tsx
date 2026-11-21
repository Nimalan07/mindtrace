"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

export interface StudentOption {
  id: string;
  label: string;
  badge: string;
}

export const KNOWN_STUDENTS: StudentOption[] = [
  { id: "student_integration_01", label: "Integration Student (Active)", badge: "Integration Test" },
  { id: "student_alice", label: "Alice (Benchmark)", badge: "Benchmark Fixture" },
  { id: "student_demo", label: "Demo Student", badge: "Demo Account" },
];

interface StudentContextType {
  currentStudentId: string;
  setCurrentStudentId: (id: string) => void;
  availableStudents: StudentOption[];
}

const StudentContext = createContext<StudentContextType | undefined>(undefined);

export function StudentProvider({ children }: { children: ReactNode }) {
  const [currentStudentId, setCurrentStudentId] = useState<string>("student_integration_01");

  return (
    <StudentContext.Provider
      value={{
        currentStudentId,
        setCurrentStudentId,
        availableStudents: KNOWN_STUDENTS,
      }}
    >
      {children}
    </StudentContext.Provider>
  );
}

export function useStudent(): StudentContextType {
  const context = useContext(StudentContext);
  if (!context) {
    throw new Error("useStudent must be used within a StudentProvider");
  }
  return context;
}
