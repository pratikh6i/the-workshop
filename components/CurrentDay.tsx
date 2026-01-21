"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

interface CurrentDayProps {
    day: {
        slug: string;
        dayNumber: number;
        title: string;
        description: string;
        date?: string;
        readingTime?: string;
        tags?: string[];
    } | null;
}

export default function CurrentDay({ day }: CurrentDayProps) {
    if (!day) {
        return (
            <div className="border border-slate-100 rounded-lg p-8 bg-slate-50 text-center">
                <h2 className="text-xl font-bold mb-3 text-slate-800">Ready to start?</h2>
                <p className="text-slate-500 mb-6">
                    Create your first entry to begin the journey.
                </p>
                <code className="inline-block bg-white border border-slate-200 rounded px-4 py-2 text-sm text-slate-600 font-mono">
                    npm run new-day
                </code>
            </div>
        );
    }

    return (
        <section className="mb-16">
            <div className="mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-sm font-semibold tracking-wide text-slate-500 uppercase">Latest Entry</span>
            </div>

            <Link href={`/day/${day.slug}/`} className="group block">
                <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 mb-6 leading-tight tracking-tight group-hover:text-slate-700 transition-colors text-balance">
                    {day.title}
                </h1>

                <p className="text-xl text-slate-600 mb-8 leading-relaxed max-w-2xl text-balance">
                    {day.description}
                </p>

                <div className="flex items-center gap-6 text-sm text-slate-500 font-medium">
                    <span className="uppercase tracking-wider text-xs font-bold text-slate-400">Day {day.dayNumber}</span>
                    <span>{day.readingTime || "5 min read"}</span>
                    <span className="text-slate-900 flex items-center group-hover:translate-x-1 transition-transform ml-auto">
                        Read Story <ArrowRight className="w-4 h-4 ml-2" />
                    </span>
                </div>
            </Link>
        </section>
    );
}
