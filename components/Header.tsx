"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Search, Github, BookOpen } from "lucide-react";

export default function Header() {
    const [scrolled, setScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 10);
        };

        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, []);

    const openCommandPalette = () => {
        // Dispatch custom event to open command palette
        window.dispatchEvent(new CustomEvent("open-command-palette"));
    };

    return (
        <motion.header
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className={`
        fixed top-0 right-0 left-0 lg:left-[280px] z-40
        h-16 px-4 lg:px-8
        flex items-center justify-between
        transition-all duration-300
        ${scrolled ? "glass-strong shadow-soft" : "bg-transparent"}
      `}
        >
            {/* Left Section */}
            <div className="flex items-center gap-4 ml-12 lg:ml-0">
                <Link
                    href="/"
                    className="flex items-center gap-2 text-slate-700 hover:text-sky-600 transition-colors"
                >
                    <BookOpen className="w-5 h-5" />
                    <span className="font-medium hidden sm:inline">Documentation</span>
                </Link>
            </div>

            {/* Center - Search Bar */}
            <button
                onClick={openCommandPalette}
                className="
          hidden md:flex items-center gap-3
          px-4 py-2 rounded-xl
          bg-white/60 hover:bg-white/80
          border border-slate-200/50
          text-slate-500 hover:text-slate-700
          transition-all duration-200
          shadow-sm hover:shadow
          min-w-[280px]
        "
            >
                <Search className="w-4 h-4" />
                <span className="text-sm">Search documentation...</span>
                <kbd className="ml-auto text-xs px-2 py-0.5 bg-slate-100 rounded font-mono text-slate-500">
                    ⌘K
                </kbd>
            </button>

            {/* Right Section */}
            <div className="flex items-center gap-3">
                {/* Mobile Search */}
                <button
                    onClick={openCommandPalette}
                    className="p-2 rounded-lg hover:bg-slate-100 md:hidden btn-press"
                    aria-label="Search"
                >
                    <Search className="w-5 h-5 text-slate-600" />
                </button>

                {/* GitHub Link */}
                <a
                    href="https://github.com/pratikh6i/the-workshop"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 rounded-lg hover:bg-slate-100 btn-press"
                    aria-label="View on GitHub"
                >
                    <Github className="w-5 h-5 text-slate-600" />
                </a>
            </div>
        </motion.header>
    );
}
