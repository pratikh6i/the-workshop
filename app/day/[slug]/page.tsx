import { notFound } from "next/navigation";
import Link from "next/link";
import { getAllDays, getDayBySlug, getAdjacentDays } from "@/lib/content";
import { MDXRemote } from "next-mdx-remote/rsc";
import { ArrowLeft, ArrowRight, Clock, Calendar, BarChart3 } from "lucide-react";
import MDXComponents from "@/components/MDXComponents";

interface PageProps {
    params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
    const days = getAllDays();
    return days.map((day) => ({
        slug: day.slug,
    }));
}

export default async function DayPage({ params }: PageProps) {
    const { slug } = await params;
    const day = getDayBySlug(slug);

    if (!day) {
        notFound();
    }

    const { prev, next } = getAdjacentDays(slug);

    const difficultyColors = {
        beginner: "tag-mint",
        intermediate: "tag-sky",
        advanced: "tag-coral",
    };

    const statusLabels = {
        completed: "Completed",
        "in-progress": "In Progress",
        draft: "Draft",
        upcoming: "Upcoming",
    };

    return (
        <article className="animate-fade-in">
            {/* Back Link */}
            <Link
                href="/"
                className="inline-flex items-center gap-2 text-slate-500 hover:text-sky-600 mb-8 btn-press"
            >
                <ArrowLeft className="w-4 h-4" />
                Back to Feed
            </Link>

            {/* Header */}
            <header className="mb-8">
                <div className="flex flex-wrap items-center gap-3 mb-4">
                    <span className="text-sm font-medium text-sky-600">
                        Day {day.dayNumber.toString().padStart(2, "0")}
                    </span>
                    <span className={`tag ${difficultyColors[day.difficulty]}`}>
                        {day.difficulty}
                    </span>
                    <span className="tag tag-slate">
                        {statusLabels[day.status]}
                    </span>
                </div>

                <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
                    {day.title}
                </h1>

                {day.description && (
                    <p className="text-lg text-slate-600 mb-6">
                        {day.description}
                    </p>
                )}

                {/* Meta */}
                <div className="flex flex-wrap items-center gap-6 text-sm text-slate-500 pb-6 border-b border-slate-200">
                    <span className="flex items-center gap-1.5">
                        <Calendar className="w-4 h-4" />
                        {new Date(day.date).toLocaleDateString("en-US", {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                        })}
                    </span>
                    {day.readingTime && (
                        <span className="flex items-center gap-1.5">
                            <Clock className="w-4 h-4" />
                            {day.readingTime}
                        </span>
                    )}
                    <span className="flex items-center gap-1.5">
                        <BarChart3 className="w-4 h-4" />
                        {day.difficulty}
                    </span>
                </div>
            </header>

            {/* Content */}
            <div className="prose max-w-none">
                {day.content && (
                    <MDXRemote source={day.content} components={MDXComponents} />
                )}
            </div>

            {/* Tags */}
            {day.tags && day.tags.length > 0 && (
                <div className="mt-12 pt-6 border-t border-slate-200">
                    <h3 className="text-sm font-medium text-slate-500 mb-3">Topics</h3>
                    <div className="flex flex-wrap gap-2">
                        {day.tags.map((tag) => (
                            <span key={tag} className="tag tag-slate">
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Navigation */}
            <nav className="mt-12 pt-8 border-t border-slate-200">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {prev && (
                        <Link
                            href={`/day/${prev.slug}`}
                            className="group p-4 rounded-xl bg-white/60 hover:bg-white border border-slate-200/50 transition-all card-hover"
                        >
                            <span className="text-xs text-slate-400 flex items-center gap-1 mb-1">
                                <ArrowLeft className="w-3 h-3" />
                                Previous
                            </span>
                            <span className="font-medium text-slate-700 group-hover:text-sky-600">
                                Day {prev.dayNumber}: {prev.title}
                            </span>
                        </Link>
                    )}
                    {next && (
                        <Link
                            href={`/day/${next.slug}`}
                            className="group p-4 rounded-xl bg-white/60 hover:bg-white border border-slate-200/50 transition-all card-hover md:text-right md:ml-auto"
                        >
                            <span className="text-xs text-slate-400 flex items-center gap-1 mb-1 md:justify-end">
                                Next
                                <ArrowRight className="w-3 h-3" />
                            </span>
                            <span className="font-medium text-slate-700 group-hover:text-sky-600">
                                Day {next.dayNumber}: {next.title}
                            </span>
                        </Link>
                    )}
                </div>
            </nav>
        </article>
    );
}
