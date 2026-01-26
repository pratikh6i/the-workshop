import fs from "fs";
import path from "path";
import matter from "gray-matter";
import { DayEntry } from "./types";

const contentDirectory = path.join(process.cwd(), "content");

export function getAllDays(): DayEntry[] {
    if (!fs.existsSync(contentDirectory)) {
        return [];
    }

    const folders = fs.readdirSync(contentDirectory);

    const days: DayEntry[] = folders
        .filter((folder) => folder.startsWith("day-"))
        .map((folder) => {
            const mdxPath = path.join(contentDirectory, folder, "index.mdx");

            if (!fs.existsSync(mdxPath)) {
                return null;
            }

            const fileContents = fs.readFileSync(mdxPath, "utf8");
            const { data, content } = matter(fileContents);

            const dayMatch = folder.match(/day-(\d+)/);
            const dayNumber = dayMatch ? parseInt(dayMatch[1], 10) : 0;

            const wordCount = content.split(/\s+/).length;
            const readingTime = `${Math.max(1, Math.ceil(wordCount / 200))} min read`;

            return {
                slug: folder,
                dayNumber,
                title: data.title || `Day ${dayNumber}`,
                date: data.date || new Date().toISOString(),
                status: data.status || "draft",
                difficulty: data.difficulty || "beginner",
                description: data.description || "",
                tags: data.tags || [],
                readingTime,
                content,
                stars: data.stars || 0,
            } as DayEntry;
        })
        .filter((day): day is DayEntry => day !== null);

    return days.sort((a, b) => b.dayNumber - a.dayNumber);
}

export function getDayBySlug(slug: string): DayEntry | null {
    const allDays = getAllDays();
    return allDays.find((day) => day.slug === slug) || null;
}

export function getCurrentDay(): DayEntry | null {
    const allDays = getAllDays();
    const inProgress = allDays.find((day) => day.status === "in-progress");
    if (inProgress) return inProgress;
    const active = allDays.find((day) => day.status !== "upcoming");
    return active || null;
}

export function getAdjacentDays(slug: string): { prev: DayEntry | null; next: DayEntry | null } {
    const allDays = getAllDays().sort((a, b) => a.dayNumber - b.dayNumber);
    const currentIndex = allDays.findIndex((day) => day.slug === slug);

    return {
        prev: currentIndex > 0 ? allDays[currentIndex - 1] : null,
        next: currentIndex < allDays.length - 1 ? allDays[currentIndex + 1] : null,
    };
}

export function getProgress(): { completed: number; total: number; percentage: number } {
    const allDays = getAllDays();
    const completed = allDays.filter((day) => day.status === "completed").length;
    const total = 90;

    return {
        completed,
        total,
        percentage: Math.round((completed / total) * 100),
    };
}
