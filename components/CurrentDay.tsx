"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Clock, Zap } from "lucide-react";

interface CurrentDayProps {
    day: {
        slug: string;
        dayNumber: number;
        title: string;
        description: string;
        readingTime?: string;
        tags?: string[];
    } | null;
}

export default function CurrentDay({ day }: CurrentDayProps) {
    if (!day) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-sky-500 to-indigo-600 p-8 text-white shadow-xl"
            >
                <div className="relative z-10">
                    <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 text-sm font-medium mb-4">
                        <Zap className="w-4 h-4" />
                        Getting Started
                    </span>
                    <h2 className="text-3xl font-bold mb-3">Welcome to The Workshop</h2>
                    <p className="text-white/80 text-lg mb-6 max-w-xl">
                        Begin your 90-day security odyssey. Create your first day entry to get started.
                    </p>
                    <div className="flex items-center gap-4">
                        <code className="px-4 py-2 bg-white/10 rounded-lg font-mono text-sm">
                            node scripts/new-day.js 1 "Your First Topic"
                        </code>
                    </div>
                </div>

                {/* Decorative Elements */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
                <div className="absolute bottom-0 left-0 w-48 h-48 bg-indigo-400/20 rounded-full blur-2xl" />
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-sky-500 via-sky-600 to-indigo-600 p-8 text-white shadow-xl"
        >
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-10">
                <div className="absolute top-0 right-0 w-96 h-96 bg-white rounded-full blur-3xl transform translate-x-1/2 -translate-y-1/2" />
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-indigo-300 rounded-full blur-2xl transform -translate-x-1/3 translate-y-1/3" />
            </div>

            <div className="relative z-10">
                {/* Status Badge */}
                <div className="flex items-center gap-3 mb-4">
                    <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 text-sm font-medium backdrop-blur-sm">
                        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                        Currently Active
                    </span>
                    <span className="text-white/70 text-sm">
                        Day {day.dayNumber.toString().padStart(2, "0")} of 90
                    </span>
                </div>

                {/* Title */}
                <h2 className="text-3xl md:text-4xl font-bold mb-3 tracking-tight">
                    {day.title}
                </h2>

                {/* Description */}
                <p className="text-white/80 text-lg mb-6 max-w-2xl leading-relaxed">
                    {day.description || "Continue your security learning journey where you left off."}
                </p>

                {/* Meta Info */}
                <div className="flex flex-wrap items-center gap-4 mb-6">
                    {day.readingTime && (
                        <span className="flex items-center gap-1.5 text-white/70 text-sm">
                            <Clock className="w-4 h-4" />
                            {day.readingTime}
                        </span>
                    )}
                    {day.tags && day.tags.map((tag) => (
                        <span
                            key={tag}
                            className="px-2.5 py-1 rounded-full bg-white/15 text-xs font-medium"
                        >
                            {tag}
                        </span>
                    ))}
                </div>

                {/* Action Button */}
                <Link
                    href={`/day/${day.slug}`}
                    className="
            inline-flex items-center gap-2 px-6 py-3
            bg-white text-sky-600 font-semibold
            rounded-xl shadow-lg
            hover:shadow-xl hover:scale-[1.02]
            active:scale-[0.98]
            transition-all duration-200
          "
                >
                    Resume Learning
                    <ArrowRight className="w-4 h-4" />
                </Link>
            </div>
        </motion.div>
    );
}
