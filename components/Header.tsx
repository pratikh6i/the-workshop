"use client";

import { useState, useEffect } from "react";
import { Search } from "lucide-react";

export default function Header() {
    const [scrolled, setScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => setScrolled(window.scrollY > 0);
        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, []);

    return (
        <header className="h-full flex items-center justify-between px-8">
            <nav className="flex items-center gap-6">
                <a
                    href="/the-workshop/"
                    className="text-sm font-medium text-slate-900 hover:text-slate-600 transition-colors"
                >
                    Security Journey
                </a>
                <a
                    href="/the-workshop/sunflower/"
                    className="text-sm font-medium text-slate-900 hover:text-slate-600 transition-colors"
                >
                    Sunflower 🌻
                </a>
            </nav>

            <button
                onClick={() => {
                    const event = new KeyboardEvent("keydown", { key: "k", metaKey: true });
                    document.dispatchEvent(event);
                }}
                className="flex items-center gap-3 px-4 py-2 text-sm text-slate-600 bg-white border border-slate-200 rounded-lg hover:border-slate-300 hover:bg-slate-50 transition-all duration-200 shadow-sm hover:shadow"
            >
                <Search className="w-4 h-4 text-slate-400" />
                <span className="font-medium">Search</span>
                <kbd className="ml-auto text-xs font-semibold text-slate-500 bg-slate-100 px-2 py-1 rounded border border-slate-200">⌘K</kbd>
            </button>
        </header>
    );
}
