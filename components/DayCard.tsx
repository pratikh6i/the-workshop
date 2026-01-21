"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Clock, CheckCircle2, Circle, ArrowRight } from "lucide-react";

interface DayCardProps {
    day: {
        slug: string;
        dayNumber: number;
        title: string;
        description: string;
        status: "completed" | "in-progress" | "draft" | "upcoming";
        difficulty: "beginner" | "intermediate" | "advanced";
        readingTime?: string;
        tags?: string[];
    };
    index: number;
}

const difficultyColors = {
    beginner: "tag-mint",
    intermediate: "tag-sky",
    advanced: "tag-coral",
};

const statusIcons = {
    completed: <CheckCircle2 className="w-5 h-5 text-green-500" />,
    "in-progress": <Circle className="w-5 h-5 text-sky-500 animate-pulse" />,
    draft: <Circle className="w-5 h-5 text-slate-400" />,
    upcoming: <Circle className="w-5 h-5 text-slate-300" />,
};

export default function DayCard({ day, index }: DayCardProps) {
    return (
        <motion.article
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="group"
        >
            <Link
                href={`/day/${day.slug}`}
                className="
          block p-6 rounded-2xl
          bg-white/60 hover:bg-white/90
          border border-white/50 hover:border-sky-200/50
          shadow-soft hover:shadow-glass-lg
          transition-all duration-300
          card-hover
        "
            >
                <div className="flex items-start gap-4">
                    {/* Status Icon */}
                    <div className="flex-shrink-0 mt-1">
                        {statusIcons[day.status]}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                        {/* Header */}
                        <div className="flex items-center gap-3 mb-2">
                            <span className="text-sm font-medium text-sky-600">
                                Day {day.dayNumber.toString().padStart(2, "0")}
                            </span>
                            <span className={`tag ${difficultyColors[day.difficulty]}`}>
                                {day.difficulty}
                            </span>
                        </div>

                        {/* Title */}
                        <h3 className="text-lg font-semibold text-slate-800 mb-2 group-hover:text-sky-700 transition-colors">
                            {day.title}
                        </h3>

                        {/* Description */}
                        {day.description && (
                            <p className="text-slate-600 text-sm leading-relaxed mb-3 line-clamp-2">
                                {day.description}
                            </p>
                        )}

                        {/* Footer */}
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3 text-sm text-slate-500">
                                {day.readingTime && (
                                    <span className="flex items-center gap-1">
                                        <Clock className="w-3.5 h-3.5" />
                                        {day.readingTime}
                                    </span>
                                )}
                                {day.tags && day.tags.slice(0, 2).map((tag) => (
                                    <span key={tag} className="tag tag-slate">
                                        {tag}
                                    </span>
                                ))}
                            </div>

                            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-sky-500 group-hover:translate-x-1 transition-all" />
                        </div>
                    </div>
                </div>
            </Link>
        </motion.article>
    );
}
