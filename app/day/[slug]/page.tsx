import { notFound } from "next/navigation";
import Link from "next/link";
import { getAllDays, getDayBySlug, getAdjacentDays } from "@/lib/content";
import { MDXRemote } from "next-mdx-remote/rsc";
import { ArrowLeft, ArrowRight, Clock, Calendar } from "lucide-react";
import MDXComponents from "@/components/MDXComponents";
import remarkGfm from "remark-gfm";

interface PageProps {
    params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
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
        beginner: "bg-emerald-50 text-emerald-700 border-emerald-100",
        intermediate: "bg-sky-50 text-sky-700 border-sky-100",
        advanced: "bg-amber-50 text-amber-700 border-amber-100",
    };

    const statusLabels = {
        completed: "Completed",
        "in-progress": "In Progress",
        draft: "Draft",
        upcoming: "Upcoming",
    };

    return (
        <article className="animate-fade-in min-h-screen pb-20">
            {/* Back Link */}
            <Link
                href="/"
                className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-900 mb-8 text-sm font-medium transition-colors no-underline"
            >
                <ArrowLeft className="w-4 h-4" />
                Back to Feed
            </Link>

            {/* Header */}
            <header className="mb-12">
                <div className="flex flex-wrap items-center gap-3 mb-6">
                    <span className="text-sm font-mono font-medium text-slate-400 uppercase">
                        {day.dayNumber > 0 ? `Day ${day.dayNumber.toString().padStart(2, "0")}` : `Special Ops ${Math.abs(day.dayNumber)}`}
                    </span>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${difficultyColors[day.difficulty] || "bg-slate-50 text-slate-600 border-slate-100"}`}>
                        {day.difficulty}
                    </span>
                </div>

                <h1 className="text-3xl md:text-5xl font-bold text-slate-900 mb-6 tracking-tight leading-tight text-balance">
                    {day.title}
                </h1>

                {day.description && (
                    <p className="text-xl text-slate-600 mb-8 leading-relaxed max-w-2xl text-balance">
                        {day.description}
                    </p>
                )}

                {/* Meta */}
                <div className="flex flex-wrap items-center gap-6 text-sm text-slate-500 py-6 border-y border-slate-100">
                    <div className="flex items-center gap-2">
                        <img
                            src="https://github.com/pratikh6i.png"
                            alt="Author"
                            className="w-8 h-8 rounded-full border border-slate-100 bg-slate-50"
                        />
                        <span className="font-medium text-slate-900">Pratik Shetti</span>
                    </div>
                    <span className="text-slate-300">•</span>
                    <span className="flex items-center gap-1.5">
                        <Calendar className="w-4 h-4" />
                        {new Date(day.date).toLocaleDateString("en-US", {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                        })}
                    </span>
                    <span className="text-slate-300">•</span>
                    {day.readingTime && (
                        <span className="flex items-center gap-1.5">
                            <Clock className="w-4 h-4" />
                            {day.readingTime}
                        </span>
                    )}
                </div>
            </header>

            {/* Content */}
            <div className="prose prose-slate prose-lg max-w-none">
                {day.content && (
                    <MDXRemote
                        source={day.content}
                        components={MDXComponents}
                        options={{
                            mdxOptions: {
                                remarkPlugins: [remarkGfm],
                            }
                        }}
                    />
                )}
            </div>

            {/* Tags */}
            {day.tags && day.tags.length > 0 && (
                <div className="mt-16 pt-8 border-t border-slate-100">
                    <h3 className="text-sm font-semibold text-slate-900 mb-4 uppercase tracking-wider">Topics</h3>
                    <div className="flex flex-wrap gap-2">
                        {day.tags.map((tag) => (
                            <span key={tag} className="px-3 py-1 bg-slate-50 text-slate-600 text-sm rounded-md border border-slate-100 hover:border-slate-300 hover:bg-white transition-all cursor-default">
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Navigation */}
            <nav className="mt-16 pt-8 border-t border-slate-100">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {prev ? (
                        <Link
                            href={`/day/${prev.slug}/`}
                            className="group p-6 rounded-xl border border-slate-100 hover:border-slate-300 hover:bg-slate-50 transition-all"
                        >
                            <span className="text-xs text-slate-400 flex items-center gap-1 mb-3 font-medium uppercase tracking-wider">
                                <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" />
                                {prev.dayNumber > 0 ? "Previous Day" : "Previous Lab"}
                            </span>
                            <div className="font-bold text-slate-800 text-lg group-hover:text-slate-900 leading-snug">
                                {prev.title}
                            </div>
                        </Link>
                    ) : <div />}

                    {next && (
                        <Link
                            href={`/day/${next.slug}/`}
                            className="group p-6 rounded-xl border border-slate-100 hover:border-slate-300 hover:bg-slate-50 transition-all md:text-right"
                        >
                            <span className="text-xs text-slate-400 flex items-center justify-end gap-1 mb-3 font-medium uppercase tracking-wider">
                                {next.dayNumber > 0 ? "Next Day" : "Next Lab"}
                                <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                            </span>
                            <div className="font-bold text-slate-800 text-lg group-hover:text-slate-900 leading-snug">
                                {next.title}
                            </div>
                        </Link>
                    )}
                </div>
            </nav>
        </article>
    );
}
