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
    content?: string; // Full blog post content for searching
}

interface CommandPaletteProps {
    items: SearchItem[];
}

export default function CommandPalette({ items }: CommandPaletteProps) {
    const [open, setOpen] = useState(false);
    const [search, setSearch] = useState("");
    const router = useRouter();

    // Keyboard shortcut
    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setOpen(o => !o);
            }
            if (e.key === "Escape") setOpen(false);
        };
        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    }, []);

    // Custom event listener
    useEffect(() => {
        const handleOpen = () => setOpen(true);
        window.addEventListener("open-command-palette", handleOpen);
        return () => window.removeEventListener("open-command-palette", handleOpen);
    }, []);

    const handleSelect = useCallback((slug: string) => {
        setOpen(false);
        setSearch("");
        router.push(`/day/${slug}/`);
    }, [router]);

    const filteredItems = items.filter(item => {
        const q = search.toLowerCase();
        return (
            item.title.toLowerCase().includes(q) ||
            item.description.toLowerCase().includes(q) ||
            (item.content && item.content.toLowerCase().includes(q)) ||
            `day ${item.dayNumber}`.includes(q)
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
                        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[100]"
                        onClick={() => setOpen(false)}
                    />

                    {/* Dialog */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.96 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.96 }}
                        className="fixed top-[15%] left-1/2 -translate-x-1/2 z-[101] w-full max-w-lg px-4"
                    >
                        <Command className="rounded-2xl overflow-hidden" loop>
                            <div className="flex items-center gap-3 px-4 py-3 bg-white border-b border-slate-200">
                                <Search className="w-5 h-5 text-slate-400" />
                                <Command.Input
                                    value={search}
                                    onValueChange={setSearch}
                                    placeholder="Search days..."
                                    className="flex-1 bg-transparent outline-none text-slate-700 placeholder:text-slate-400"
                                    autoFocus
                                />
                                <button onClick={() => setOpen(false)} className="p-1 hover:bg-slate-100 rounded">
                                    <X className="w-4 h-4 text-slate-400" />
                                </button>
                            </div>

                            <Command.List className="max-h-72 overflow-y-auto bg-white">
                                <Command.Empty className="py-6 text-center text-slate-500 text-sm">
                                    No results found
                                </Command.Empty>

                                {filteredItems.map(item => (
                                    <Command.Item
                                        key={item.slug}
                                        value={`${item.title} day ${item.dayNumber}`}
                                        onSelect={() => handleSelect(item.slug)}
                                        className="flex items-center gap-3 px-4 py-3 cursor-pointer data-[selected=true]:bg-slate-50 group"
                                    >
                                        <div className="w-9 h-9 rounded-lg bg-sky-100 flex items-center justify-center">
                                            <FileText className="w-4 h-4 text-sky-600" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <span className="text-xs font-medium text-sky-600">
                                                Day {item.dayNumber.toString().padStart(2, "0")}
                                            </span>
                                            <p className="font-medium text-slate-700 text-sm truncate">{item.title}</p>
                                        </div>
                                        <ArrowRight className="w-4 h-4 text-slate-300 group-data-[selected=true]:text-slate-500" />
                                    </Command.Item>
                                ))}
                            </Command.List>

                            <div className="flex items-center justify-between px-4 py-2 bg-slate-50 border-t border-slate-200 text-xs text-slate-500">
                                <span>↑↓ Navigate</span>
                                <span>↵ Open</span>
                                <span>Esc Close</span>
                            </div>
                        </Command>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
