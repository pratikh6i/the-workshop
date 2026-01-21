"use client";

import Link from "next/link";
import { Calendar, Clock } from "lucide-react";

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
            <div className="border border-gray-200 rounded-lg p-8 bg-white">
                <h2 className="text-xl font-bold mb-3">No posts yet</h2>
                <p className="text-gray-600 mb-4">
                    Start your journey by creating your first post.
                </p>
                <code className="block bg-gray-50 border border-gray-200 rounded p-3 text-sm">
                    node scripts/new-day.js 1 "Your First Topic"
                </code>
            </div>
        );
    }

    return (
        <div className="border-2 border-black rounded-lg p-8 bg-white mb-8">
            <div className="flex items-center gap-3 mb-4">
                <span className="text-xs font-bold uppercase tracking-wide text-gray-500">
                    Day {day.dayNumber}
                </span>
                {day.tags && day.tags.slice(0, 2).map(tag => (
                    <span key={tag} className="tag">
                        {tag}
                    </span>
                ))}
            </div>

            <h1 className="text-3xl font-bold mb-4">{day.title}</h1>

            <p className="text-gray-600 mb-6 text-lg">
                {day.description}
            </p>

            <div className="flex items-center gap-6 text-sm text-gray-500 mb-6">
                {day.date && (
                    <span className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        {new Date(day.date).toLocaleDateString("en-US", {
                            month: "long",
                            day: "numeric",
                            year: "numeric"
                        })}
                    </span>
                )}
                {day.readingTime && (
                    <span className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        {day.readingTime}
                    </span>
                )}
            </div>

            <Link
                href={`/day/${day.slug}/`}
                className="inline-block px-6 py-2.5 bg-black text-white font-medium rounded hover:bg-gray-800 transition-colors"
            >
                Read Post →
            </Link>
        </div>
    );
}
