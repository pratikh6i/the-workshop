"use client";

import Link from "next/link";
import { Calendar, Clock } from "lucide-react";

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
    };
    index: number;
}

export default function DayCard({ day }: DayCardProps) {
    return (
        <Link href={`/day/${day.slug}/`} className="card block">
            <div className="flex items-start gap-4">
                <div className="text-sm font-bold text-gray-400">
                    {day.dayNumber.toString().padStart(2, '0')}
                </div>
                <div className="flex-1">
                    <h3 className="font-semibold text-black mb-2 leading-tight">
                        {day.title}
                    </h3>
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {day.description}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                        {day.date && (
                            <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {new Date(day.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                            </span>
                        )}
                        {day.readingTime && (
                            <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {day.readingTime}
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </Link>
    );
}
