import type { MDXComponents as MDXComponentsType } from "mdx/types";
import { AlertCircle, Info, Lightbulb, AlertTriangle, CheckCircle2 } from "lucide-react";

const MDXComponents: MDXComponentsType = {
    // Headings - Medium Style
    h1: ({ children }) => (
        <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mt-10 mb-6 tracking-tight leading-tight">
            {children}
        </h1>
    ),
    h2: ({ children }) => (
        <h2 className="text-2xl font-bold text-slate-900 mt-10 mb-4 tracking-tight leading-snug">
            {children}
        </h2>
    ),
    h3: ({ children }) => (
        <h3 className="text-xl font-bold text-slate-900 mt-8 mb-3 tracking-tight">
            {children}
        </h3>
    ),
    h4: ({ children }) => (
        <h4 className="text-lg font-semibold text-slate-800 mt-6 mb-2 tracking-tight">
            {children}
        </h4>
    ),

    // Paragraphs - Editorial
    p: ({ children }) => (
        <p className="text-lg text-slate-700 leading-8 mb-6 font-normal">
            {children}
        </p>
    ),

    // Lists
    ul: ({ children }) => (
        <ul className="list-disc list-outside space-y-2 mb-6 text-lg text-slate-700 leading-8 pl-5">
            {children}
        </ul>
    ),
    ol: ({ children }) => (
        <ol className="list-decimal list-outside space-y-2 mb-6 text-lg text-slate-700 leading-8 pl-5">
            {children}
        </ol>
    ),
    li: ({ children }) => <li className="pl-1 text-slate-700">{children}</li>,

    // Links
    a: ({ href, children }) => (
        <a
            href={href}
            className="text-slate-900 border-b border-slate-300 hover:border-slate-900 hover:bg-slate-50 transition-all font-medium pb-0.5 no-underline"
            target={href?.startsWith("http") ? "_blank" : undefined}
            rel={href?.startsWith("http") ? "noopener noreferrer" : undefined}
        >
            {children}
        </a>
    ),

    // Code - Clean & Minimal
    code: ({ children }) => (
        <code className="px-1.5 py-0.5 bg-slate-100/80 text-slate-800 rounded-md text-[0.9em] font-mono border border-slate-200/50">
            {children}
        </code>
    ),
    pre: ({ children }) => (
        <div className="relative mb-8 mt-6">
            <pre className="overflow-x-auto rounded-lg border border-slate-200 bg-slate-50 p-5 text-sm leading-relaxed text-slate-800 shadow-sm font-mono scrollbar-hide">
                {children}
            </pre>
        </div>
    ),

    // Blockquote
    blockquote: ({ children }) => (
        <blockquote className="border-l-[3px] border-slate-900 pl-6 py-1 my-8 text-xl italic text-slate-800 leading-relaxed bg-transparent">
            {children}
        </blockquote>
    ),

    // Horizontal Rule
    hr: () => <hr className="my-10 border-slate-100" />,

    // Strong and Emphasis
    strong: ({ children }) => (
        <strong className="font-bold text-slate-900">{children}</strong>
    ),
    em: ({ children }) => <em className="italic text-slate-800 font-medium">{children}</em>,

    // Tables
    table: ({ children }) => (
        <div className="overflow-x-auto my-8 border rounded-lg border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                {children}
            </table>
        </div>
    ),
    thead: ({ children }) => <thead className="bg-slate-50 font-medium text-slate-900">{children}</thead>,
    tbody: ({ children }) => (
        <tbody className="divide-y divide-slate-200 bg-white">{children}</tbody>
    ),
    tr: ({ children }) => <tr className="hover:bg-slate-50/50 transition-colors">{children}</tr>,
    th: ({ children }) => (
        <th className="px-4 py-3 font-semibold text-slate-900">{children}</th>
    ),
    td: ({ children }) => (
        <td className="px-4 py-3 text-slate-600">{children}</td>
    ),

    // Images
    img: ({ src, alt }) => (
        <figure className="my-10 group">
            <div className="overflow-hidden rounded-lg border border-slate-100 shadow-sm">
                <img
                    src={src}
                    alt={alt || ""}
                    className="w-full h-auto object-cover transition-transform duration-500 group-hover:scale-[1.01]"
                />
            </div>
            {alt && (
                <figcaption className="text-center text-sm text-slate-500 mt-3 font-medium">
                    {alt}
                </figcaption>
            )}
        </figure>
    ),

    // Custom Callout - Refined
    Callout: ({ type = "info", children }: { type?: "info" | "warning" | "tip" | "danger" | "success"; children: React.ReactNode }) => {
        const styles = {
            info: { bg: "bg-slate-50", border: "border-slate-200", text: "text-slate-800", icon: <Info className="w-5 h-5 text-slate-500" /> },
            warning: { bg: "bg-amber-50", border: "border-amber-100", text: "text-amber-900", icon: <AlertTriangle className="w-5 h-5 text-amber-600" /> },
            tip: { bg: "bg-emerald-50", border: "border-emerald-100", text: "text-emerald-900", icon: <Lightbulb className="w-5 h-5 text-emerald-600" /> },
            success: { bg: "bg-emerald-50", border: "border-emerald-100", text: "text-emerald-900", icon: <CheckCircle2 className="w-5 h-5 text-emerald-600" /> },
            danger: { bg: "bg-red-50", border: "border-red-100", text: "text-red-900", icon: <AlertCircle className="w-5 h-5 text-red-600" /> },
        };
        const style = styles[type] || styles.info;

        return (
            <div className={`flex gap-4 p-5 rounded-lg ${style.bg} border ${style.border} my-8`}>
                <div className="flex-shrink-0 mt-0.5">{style.icon}</div>
                <div className={`text-base leading-7 ${style.text} flex-1`}>{children}</div>
            </div>
        );
    },
};

export default MDXComponents;
