"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { motion, AnimatePresence } from "framer-motion";
import { Search, FileText, ArrowRight, X } from "lucide-react";

interface SearchItem {
    slug: string;
    dayNumber: number;
    title: string;
    description: string;
}

// Sample search items - will be hydrated with actual content
const sampleItems: SearchItem[] = [
    { slug: "day-01-introduction", dayNumber: 1, title: "Introduction to Security", description: "Getting started with the 90-day security journey" },
    { slug: "day-02-threat-modeling", dayNumber: 2, title: "Threat Modeling", description: "Understanding how to identify and analyze threats" },
    { slug: "day-03-network-basics", dayNumber: 3, title: "Network Basics", description: "Fundamentals of network security" },
];

export default function CommandPalette() {
    const [open, setOpen] = useState(false);
    const [search, setSearch] = useState("");
    const [items, setItems] = useState<SearchItem[]>(sampleItems);
    const router = useRouter();

    // Keyboard shortcut handler
    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setOpen((o) => !o);
            }
            if (e.key === "Escape") {
                setOpen(false);
            }
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    }, []);

    // Listen for custom event from header
    useEffect(() => {
        const handleOpen = () => setOpen(true);
        window.addEventListener("open-command-palette", handleOpen);
        return () => window.removeEventListener("open-command-palette", handleOpen);
    }, []);

    // Fetch items on mount
    useEffect(() => {
        async function fetchItems() {
            try {
                const res = await fetch("/api/days");
                if (res.ok) {
                    const data = await res.json();
                    if (data.length > 0) {
                        setItems(data.map((d: SearchItem) => ({
                            slug: d.slug,
                            dayNumber: d.dayNumber,
                            title: d.title,
                            description: d.description || "",
                        })));
                    }
                }
            } catch {
                // Use sample data if fetch fails
            }
        }
        fetchItems();
    }, []);

    const handleSelect = useCallback((slug: string) => {
        setOpen(false);
        setSearch("");
        router.push(`/day/${slug}`);
    }, [router]);

    const filteredItems = items.filter((item) => {
        const searchLower = search.toLowerCase();
        return (
            item.title.toLowerCase().includes(searchLower) ||
            item.description.toLowerCase().includes(searchLower) ||
            `day ${item.dayNumber}`.includes(searchLower)
        );
    });

    return (
        <AnimatePresence>
            {open && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-[100]"
                        onClick={() => setOpen(false)}
                    />

                    {/* Command Dialog */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -20 }}
                        transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        className="fixed top-[20%] left-1/2 -translate-x-1/2 z-[101] w-full max-w-xl px-4"
                    >
                        <Command
                            className="rounded-2xl overflow-hidden shadow-2xl"
                            loop
                        >
                            {/* Search Input */}
                            <div className="flex items-center gap-3 px-5 py-4 border-b border-slate-200/50 bg-white/95">
                                <Search className="w-5 h-5 text-slate-400" />
                                <Command.Input
                                    value={search}
                                    onValueChange={setSearch}
                                    placeholder="Search days, topics, or keywords..."
                                    className="flex-1 bg-transparent outline-none text-slate-700 placeholder:text-slate-400"
                                    autoFocus
                                />
                                <button
                                    onClick={() => setOpen(false)}
                                    className="p-1 rounded-md hover:bg-slate-100"
                                >
                                    <X className="w-4 h-4 text-slate-400" />
                                </button>
                            </div>

                            {/* Results */}
                            <Command.List className="max-h-80 overflow-y-auto p-2 bg-white/95">
                                <Command.Empty className="py-8 text-center text-slate-500">
                                    No results found for "{search}"
                                </Command.Empty>

                                <Command.Group heading="Days" className="px-2 py-1 text-xs font-medium text-slate-400 uppercase">
                                    {filteredItems.map((item) => (
                                        <Command.Item
                                            key={item.slug}
                                            value={`${item.title} day ${item.dayNumber}`}
                                            onSelect={() => handleSelect(item.slug)}
                                            className="flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer data-[selected=true]:bg-sky-50 group"
                                        >
                                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-sky-100 to-sky-200 flex items-center justify-center">
                                                <FileText className="w-5 h-5 text-sky-600" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs font-medium text-sky-600">
                                                        Day {item.dayNumber.toString().padStart(2, "0")}
                                                    </span>
                                                </div>
                                                <p className="font-medium text-slate-700 truncate">
                                                    {item.title}
                                                </p>
                                                {item.description && (
                                                    <p className="text-sm text-slate-500 truncate">
                                                        {item.description}
                                                    </p>
                                                )}
                                            </div>
                                            <ArrowRight className="w-4 h-4 text-slate-400 opacity-0 group-data-[selected=true]:opacity-100 transition-opacity" />
                                        </Command.Item>
                                    ))}
                                </Command.Group>
                            </Command.List>

                            {/* Footer */}
                            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200/50 bg-slate-50/50 text-xs text-slate-500">
                                <div className="flex items-center gap-4">
                                    <span className="flex items-center gap-1">
                                        <kbd className="px-1.5 py-0.5 bg-white rounded shadow-sm">↑↓</kbd>
                                        Navigate
                                    </span>
                                    <span className="flex items-center gap-1">
                                        <kbd className="px-1.5 py-0.5 bg-white rounded shadow-sm">↵</kbd>
                                        Open
                                    </span>
                                </div>
                                <span className="flex items-center gap-1">
                                    <kbd className="px-1.5 py-0.5 bg-white rounded shadow-sm">Esc</kbd>
                                    Close
                                </span>
                            </div>
                        </Command>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
