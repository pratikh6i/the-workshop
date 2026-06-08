"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, CheckCircle2, Circle, Lightbulb, Link2 } from "lucide-react";

// Types
interface ConnectingTheDotsContextType {
    mastered: Record<number, boolean>;
    toggleMastered: (id: number) => void;
    revealed: Record<number, boolean>;
    toggleRevealed: (id: number) => void;
    registerQuestion: (id: number) => void;
}

const ConnectingTheDotsContext = createContext<ConnectingTheDotsContextType | undefined>(undefined);

export function useConnectingTheDots() {
    const context = useContext(ConnectingTheDotsContext);
    if (!context) {
        throw new Error("useConnectingTheDots must be used within a ConnectingTheDots provider");
    }
    return context;
}

interface ConnectingTheDotsProps {
    children: React.ReactNode;
}

export default function ConnectingTheDots({ children }: ConnectingTheDotsProps) {
    const [mastered, setMastered] = useState<Record<number, boolean>>({});
    const [revealed, setRevealed] = useState<Record<number, boolean>>({});
    const [registeredIds, setRegisteredIds] = useState<number[]>([]);

    const registerQuestion = (id: number) => {
        setRegisteredIds((prev) => {
            if (prev.includes(id)) return prev;
            return [...prev, id].sort((a, b) => a - b);
        });
    };

    const toggleMastered = (id: number) => {
        setMastered((prev) => ({
            ...prev,
            [id]: !prev[id],
        }));
    };

    const toggleRevealed = (id: number) => {
        setRevealed((prev) => ({
            ...prev,
            [id]: !prev[id],
        }));
    };

    const totalQuestions = registeredIds.length;
    const masteredCount = Object.values(mastered).filter(Boolean).length;
    const revealedCount = Object.values(revealed).filter(Boolean).length;

    const progressPercent = totalQuestions > 0 ? Math.round((masteredCount / totalQuestions) * 100) : 0;

    return (
        <ConnectingTheDotsContext.Provider
            value={{
                mastered,
                toggleMastered,
                revealed,
                toggleRevealed,
                registerQuestion,
            }}
        >
            <div className="my-12 p-6 md:p-8 rounded-2xl border border-slate-200 bg-slate-50/50 backdrop-blur-sm shadow-sm relative overflow-hidden">
                {/* Visual Accent/Glow */}
                <div className="absolute top-0 right-0 -mt-10 -mr-10 w-40 h-40 rounded-full bg-indigo-400/10 blur-3xl pointer-events-none" />
                <div className="absolute bottom-0 left-0 -mb-10 -ml-10 w-40 h-40 rounded-full bg-purple-400/10 blur-3xl pointer-events-none" />

                {/* Header Info */}
                <div className="relative z-10 mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                        <h3 className="text-xl md:text-2xl font-bold text-slate-900 flex items-center gap-2 m-0">
                            <Link2 className="w-5 h-5 text-indigo-500" />
                            Connecting the Dots
                        </h3>
                        <p className="text-sm text-slate-500 mt-1 m-0">
                            Revise today's concepts by exploring connections and testing your memory.
                        </p>
                    </div>

                    {/* Stats Card */}
                    <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-xl border border-slate-100 shadow-sm self-start md:self-auto">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                            Progress
                        </div>
                        <div className="flex items-baseline gap-1">
                            <span className="text-lg font-bold text-slate-900">{masteredCount}</span>
                            <span className="text-xs text-slate-400">/</span>
                            <span className="text-xs text-slate-500 font-medium">{totalQuestions}</span>
                        </div>
                        <span className="text-xs text-slate-300">|</span>
                        <div className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
                            {progressPercent}%
                        </div>
                    </div>
                </div>

                {/* Global Progress Bar */}
                <div className="relative z-10 mb-8">
                    <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                        <motion.div
                            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${progressPercent}%` }}
                            transition={{ duration: 0.4, ease: "easeOut" }}
                        />
                    </div>
                    <div className="flex justify-between items-center mt-2 text-xs text-slate-400">
                        <span>Reveal connections to study</span>
                        <span>{masteredCount === totalQuestions && totalQuestions > 0 ? "🎉 Fully Connected!" : "Connect all dots to complete"}</span>
                    </div>
                </div>

                {/* Questions Container */}
                <div className="relative z-10 space-y-4">
                    {children}
                </div>
            </div>
        </ConnectingTheDotsContext.Provider>
    );
}

// Question Card Component
interface QuestionCardProps {
    id: number;
    question: string;
    children: React.ReactNode;
}

export function QuestionCard({ id, question, children }: QuestionCardProps) {
    const { mastered, toggleMastered, revealed, toggleRevealed, registerQuestion } = useConnectingTheDots();

    useEffect(() => {
        registerQuestion(id);
    }, [id]);

    const isRevealed = !!revealed[id];
    const isMastered = !!mastered[id];

    return (
        <div
            className={`border rounded-xl transition-all duration-300 bg-white shadow-xs ${
                isRevealed
                    ? "border-indigo-100 ring-1 ring-indigo-50/50"
                    : "border-slate-100 hover:border-slate-200 hover:shadow-sm"
            }`}
        >
            {/* Card Header (Clickable for Reveal) */}
            <div
                onClick={() => toggleRevealed(id)}
                className="p-5 flex items-start gap-4 cursor-pointer select-none"
            >
                {/* Question Indicator / Index */}
                <div
                    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-mono text-sm font-semibold transition-colors ${
                        isMastered
                            ? "bg-indigo-500 text-white"
                            : isRevealed
                            ? "bg-indigo-50 text-indigo-600"
                            : "bg-slate-100 text-slate-500"
                    }`}
                >
                    Q{id}
                </div>

                {/* Question Text */}
                <div className="flex-1">
                    <h4 className="text-base md:text-lg font-bold text-slate-800 leading-snug m-0 hover:text-slate-900 transition-colors">
                        {question}
                    </h4>
                </div>

                {/* Reveal Arrow */}
                <div className="flex-shrink-0 text-slate-400 self-center">
                    {isRevealed ? (
                        <ChevronUp className="w-5 h-5 text-indigo-500 transition-transform duration-200" />
                    ) : (
                        <ChevronDown className="w-5 h-5 group-hover:text-slate-600 transition-transform duration-200" />
                    )}
                </div>
            </div>

            {/* Expandable Content Panel */}
            <AnimatePresence initial={false}>
                {isRevealed && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25, ease: "easeInOut" }}
                        className="overflow-hidden"
                    >
                        <div className="px-5 pb-5 pt-1 border-t border-slate-50 bg-slate-50/30">
                            {/* The Answer Context */}
                            <div className="prose prose-slate prose-sm md:prose-base max-w-none text-slate-600 leading-relaxed my-4">
                                {children}
                            </div>

                            {/* Card Footer / Action Section */}
                            <div className="mt-5 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4">
                                <div className="flex items-center gap-1.5 text-xs text-indigo-600 bg-indigo-50/50 px-2 py-1 rounded-md">
                                    <Lightbulb className="w-3.5 h-3.5" />
                                    <span>Review connection carefully before marking</span>
                                </div>

                                {/* Connect the Dot Action Button */}
                                <button
                                    type="button"
                                    onClick={(e) => {
                                        e.stopPropagation(); // Avoid closing the card
                                        toggleMastered(id);
                                    }}
                                    className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                                        isMastered
                                            ? "bg-emerald-500 hover:bg-emerald-600 text-white shadow-xs"
                                            : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                                    }`}
                                >
                                    {isMastered ? (
                                        <>
                                            <CheckCircle2 className="w-4 h-4" />
                                            <span>Dot Connected</span>
                                        </>
                                    ) : (
                                        <>
                                            <Circle className="w-4 h-4 text-slate-400" />
                                            <span>Connect Dot</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
