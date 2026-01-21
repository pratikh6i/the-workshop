export interface DayEntry {
    slug: string;
    dayNumber: number;
    title: string;
    date: string;
    status: "completed" | "in-progress" | "draft" | "upcoming";
    difficulty: "beginner" | "intermediate" | "advanced";
    description: string;
    tags: string[];
    readingTime?: string;
    content?: string;
}

export interface NavigationItem {
    label: string;
    href: string;
    icon?: string;
}
