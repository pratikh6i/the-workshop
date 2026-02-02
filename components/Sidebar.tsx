"use client";

import Link from "next/link";
import { CheckCircle2, Circle } from "lucide-react";

interface SidebarProps {
    days: {
        slug: string;
        dayNumber: number;
        title: string;
        status: "completed" | "in-progress" | "draft" | "upcoming";
    }[];
    progress: {
        completed: number;
        total: number;
        percentage: number;
    };
}

export default function Sidebar({ days, progress }: SidebarProps) {
    const sortedDays = [...days].sort((a, b) => a.dayNumber - b.dayNumber);

    return (
        <aside className="h-full flex flex-col px-6 py-8">
            {/* Branding */}
            <div className="mb-10">
                <Link href="/" className="block">
                    <h1 className="text-xl font-bold tracking-tight text-slate-900">The Workshop</h1>
                    <p className="text-slate-500 text-sm mt-1">90-Day Security Odyssey</p>
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto pr-2 -mr-2">
                <div className="space-y-1">
                    {sortedDays.map((day) => {
                        const isActive = false; // logic would need pathname check, but component doesn't have it. 
                        // For now, rely on hover states.
                        const isCompleted = day.status === "completed";
                        const isInProgress = day.status === "in-progress";

                        return (
                            <Link
                                key={day.slug}
                                href={`/day/${day.slug}/`}
                                className={`group flex items-start gap-3 py-2 px-2 rounded-md transition-all hover:bg-slate-100 ${isActive ? "bg-slate-100" : ""
                                    }`}
                            >
                                <div className="mt-1 flex-shrink-0">
                                    {isCompleted ? (
                                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                                    ) : isInProgress ? (
                                        <div className="w-4 h-4 rounded-full border-2 border-sky-500 animate-pulse" />
                                    ) : (
                                        <span className="text-slate-300 text-xs font-mono w-4 inline-block text-center">
                                            {day.dayNumber > 0 ? day.dayNumber : `S${Math.abs(day.dayNumber)}`}
                                        </span>
                                    )}
                                </div>

                                <div className="flex-1 min-w-0">
                                    <p className={`text-sm font-medium truncate ${isCompleted ? "text-slate-500" : "text-slate-700 group-hover:text-slate-900"
                                        }`}>
                                        {day.title}
                                    </p>
                                </div>
                            </Link>
                        );
                    })}
                </div>
            </nav>

            {/* Minimal Footer / Progress */}
            <div className="mt-6 pt-6 border-t border-slate-100">
                <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                    <span>Progress</span>
                    <span>{progress.percentage}%</span>
                </div>
                <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-slate-900 rounded-full transition-all duration-1000"
                        style={{ width: `${progress.percentage}%` }}
                    />
                </div>
            </div>
        </aside>
    );
}
