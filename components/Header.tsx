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
            <div>
                <h2 className="text-sm font-medium">Security Journey</h2>
            </div>

            <button
                onClick={() => {
                    const event = new KeyboardEvent("keydown", { key: "k", metaKey: true });
                    document.dispatchEvent(event);
                }}
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 border border-gray-200 rounded hover:border-gray-300"
            >
                <Search className="w-4 h-4" />
                <span>Search</span>
                <kbd className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">⌘K</kbd>
            </button>
        </header>
    );
}
