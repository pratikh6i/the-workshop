"use client";

import Link from "next/link";

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
    return (
        <aside className="h-full flex flex-col p-6">
            {/* Simple Header */}
            <div className="mb-8">
                <h1 className="text-lg font-bold mb-1">The Workshop</h1>
                <p className="text-xs text-gray-500">90-Day Security Odyssey</p>
            </div>

            {/* Progress */}
            <div className="mb-8 pb-6 border-b border-gray-200">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-medium text-gray-600">Progress</span>
                    <span className="text-xs font-bold">{progress.percentage}%</span>
                </div>
                <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-black transition-all"
                        style={{ width: `${progress.percentage}%` }}
                    />
                </div>
                <div className="flex justify-between mt-2 text-xs text-gray-500">
                    <span>{progress.completed} done</span>
                    <span>{progress.total - progress.completed} left</span>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto">
                <div className="metro-line">
                    {days.sort((a, b) => a.dayNumber - b.dayNumber).map((day) => {
                        const isActive = day.status === "in-progress";
                        const isCompleted = day.status === "completed";

                        return (
                            <Link
                                key={day.slug}
                                href={`/day/${day.slug}/`}
                                className={`metro-node block ${isCompleted ? "completed" : ""} ${isActive ? "active" : ""}`}
                            >
                                <div className="text-xs text-gray-400 mb-1">
                                    Day {day.dayNumber.toString().padStart(2, '0')}
                                </div>
                                <div className={`text-sm font-medium ${isActive ? "text-blue-600" :
                                        isCompleted ? "text-black" :
                                            "text-gray-400"
                                    }`}>
                                    {day.title}
                                </div>
                            </Link>
                        );
                    })}
                </div>
            </nav>
        </aside>
    );
}
