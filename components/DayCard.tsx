"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

interface DayCardProps {
    day: {
        slug: string;
        dayNumber: number;
        title: string;
        description: string;
        date?: string;
        readingTime?: string;
        status: string;
        difficulty: string;
        stars?: number;
    };
    index: number;
}

export default function DayCard({ day }: DayCardProps) {
    return (
        <Link href={`/day/${day.slug}/`} className="group block mb-12 last:mb-0">
            <article className="border-b border-slate-100 pb-12 hover:border-slate-200 transition-colors">
                <div className="flex items-center gap-3 text-sm text-slate-500 mb-3 font-medium">
                    <span className="uppercase tracking-wider text-xs">Day {day.dayNumber}</span>
                    <span>•</span>
                    <span>{day.readingTime || "5 min read"}</span>
                    {day.difficulty && (
                        <>
                            <span>•</span>
                            <span className="capitalize text-slate-400">{day.difficulty}</span>
                        </>
                    )}
                </div>

                <h3 className="text-2xl font-bold text-slate-900 mb-3 group-hover:text-slate-700 transition-colors leading-tight tracking-tight flex items-center gap-2">
                    {day.title}
                    {day.stars && day.stars > 0 && (
                        <span className="text-purple-500" title="Special learning day">
                            {"⭐".repeat(day.stars)}
                        </span>
                    )}
                </h3>

                <p className="text-slate-600 text-lg leading-relaxed mb-4 line-clamp-2 max-w-2xl">
                    {day.description}
                </p>

                <div className="flex items-center text-slate-900 text-sm font-semibold group-hover:translate-x-1 transition-transform inline-flex">
                    Read Post <ArrowRight className="w-4 h-4 ml-1" />
                </div>
            </article>
        </Link>
    );
}
