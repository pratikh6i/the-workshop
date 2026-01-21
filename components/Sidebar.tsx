"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
    Menu,
    X,
    ChevronRight,
    Shield,
    Zap,
    Trophy
} from "lucide-react";

interface DayItem {
    slug: string;
    dayNumber: number;
    title: string;
    status: "completed" | "in-progress" | "draft" | "upcoming";
}

// Sample data - will be replaced with actual content
const sampleDays: DayItem[] = [
    { slug: "day-03-network-basics", dayNumber: 3, title: "Network Basics", status: "in-progress" },
    { slug: "day-02-threat-modeling", dayNumber: 2, title: "Threat Modeling", status: "completed" },
    { slug: "day-01-introduction", dayNumber: 1, title: "Introduction", status: "completed" },
];

export default function Sidebar() {
    const [isOpen, setIsOpen] = useState(false);
    const [days, setDays] = useState<DayItem[]>(sampleDays);
    const pathname = usePathname();

    // Fetch days on mount
    useEffect(() => {
        async function fetchDays() {
            try {
                const res = await fetch("/api/days");
                if (res.ok) {
                    const data = await res.json();
                    if (data.length > 0) {
                        setDays(data);
                    }
                }
            } catch {
                // Use sample data if fetch fails
            }
        }
        fetchDays();
    }, []);

    const completedCount = days.filter(d => d.status === "completed").length;
    const progressPercentage = Math.round((completedCount / 90) * 100);

    return (
        <>
            {/* Mobile Menu Button */}
            <button
                onClick={() => setIsOpen(true)}
                className="fixed top-4 left-4 z-50 lg:hidden p-2 rounded-lg glass btn-press"
                aria-label="Open menu"
            >
                <Menu className="w-5 h-5 text-slate-700" />
            </button>

            {/* Mobile Overlay */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
                        onClick={() => setIsOpen(false)}
                    />
                )}
            </AnimatePresence>

            {/* Sidebar */}
            <motion.aside
                initial={{ x: -280 }}
                animate={{ x: isOpen ? 0 : -280 }}
                className={`
          fixed top-0 left-0 z-50 h-full w-[280px]
          glass-strong border-r border-white/20
          flex flex-col
          lg:translate-x-0 lg:z-30
        `}
                style={{ transform: "none" }}
            >
                {/* Close button (mobile) */}
                <button
                    onClick={() => setIsOpen(false)}
                    className="absolute top-4 right-4 p-2 rounded-lg hover:bg-slate-100 lg:hidden"
                    aria-label="Close menu"
                >
                    <X className="w-5 h-5 text-slate-700" />
                </button>

                {/* Header */}
                <div className="p-6 border-b border-slate-200/50">
                    <Link href="/" className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 to-sky-600 flex items-center justify-center shadow-lg">
                            <Shield className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="font-semibold text-slate-900">The Workshop</h1>
                            <p className="text-xs text-slate-500">90-Day Security Odyssey</p>
                        </div>
                    </Link>
                </div>

                {/* Progress Section */}
                <div className="p-6 border-b border-slate-200/50">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-slate-700">Progress</span>
                        <span className="text-sm font-bold text-sky-600">{progressPercentage}%</span>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-2 bg-slate-200/50 rounded-full overflow-hidden">
                        <motion.div
                            className="h-full bg-gradient-to-r from-sky-400 to-mint-500 rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${progressPercentage}%` }}
                            transition={{ duration: 1, ease: "easeOut" }}
                        />
                    </div>

                    <div className="flex items-center justify-between mt-3 text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                            <Trophy className="w-3 h-3" />
                            {completedCount} completed
                        </span>
                        <span className="flex items-center gap-1">
                            <Zap className="w-3 h-3" />
                            {90 - completedCount} to go
                        </span>
                    </div>
                </div>

                {/* Metro Line Navigation */}
                <nav className="flex-1 overflow-y-auto p-4">
                    <div className="metro-line">
                        {days.map((day, index) => (
                            <motion.div
                                key={day.slug}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.05 }}
                            >
                                <Link
                                    href={`/day/${day.slug}`}
                                    className={`
                    metro-node block py-3 rounded-lg transition-colors
                    ${day.status}
                    ${pathname === `/day/${day.slug}` ? "bg-sky-50" : "hover:bg-slate-50"}
                  `}
                                >
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <span className="text-xs font-medium text-slate-400">
                                                Day {day.dayNumber.toString().padStart(2, "0")}
                                            </span>
                                            <p className={`
                        text-sm font-medium mt-0.5
                        ${day.status === "completed" ? "text-slate-700" : ""}
                        ${day.status === "in-progress" ? "text-sky-700" : ""}
                        ${day.status === "draft" ? "text-slate-500" : ""}
                        ${day.status === "upcoming" ? "text-slate-400" : ""}
                      `}>
                                                {day.title}
                                            </p>
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-slate-400" />
                                    </div>
                                </Link>
                            </motion.div>
                        ))}
                    </div>
                </nav>

                {/* Footer */}
                <div className="p-4 border-t border-slate-200/50 text-center">
                    <p className="text-xs text-slate-400">
                        Press <kbd className="px-1.5 py-0.5 bg-slate-100 rounded text-slate-600 font-mono">⌘K</kbd> to search
                    </p>
                </div>
            </motion.aside>

            {/* Desktop Sidebar - always visible */}
            <style jsx global>{`
        @media (min-width: 1024px) {
          aside {
            transform: translateX(0) !important;
          }
        }
      `}</style>
        </>
    );
}
