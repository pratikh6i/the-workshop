import type { MDXComponents as MDXComponentsType } from "mdx/types";
import { AlertCircle, Info, Lightbulb, AlertTriangle } from "lucide-react";

const MDXComponents: MDXComponentsType = {
    // Headings
    h1: ({ children }) => (
        <h1 className="text-3xl font-bold text-slate-900 mt-8 mb-4">{children}</h1>
    ),
    h2: ({ children }) => (
        <h2 className="text-2xl font-semibold text-slate-800 mt-8 mb-3 pb-2 border-b border-slate-200">
            {children}
        </h2>
    ),
    h3: ({ children }) => (
        <h3 className="text-xl font-semibold text-slate-800 mt-6 mb-3">{children}</h3>
    ),
    h4: ({ children }) => (
        <h4 className="text-lg font-semibold text-slate-700 mt-4 mb-2">{children}</h4>
    ),

    // Paragraphs
    p: ({ children }) => (
        <p className="text-slate-600 leading-relaxed mb-4">{children}</p>
    ),

    // Lists
    ul: ({ children }) => (
        <ul className="list-disc list-inside space-y-2 mb-4 text-slate-600 pl-4">
            {children}
        </ul>
    ),
    ol: ({ children }) => (
        <ol className="list-decimal list-inside space-y-2 mb-4 text-slate-600 pl-4">
            {children}
        </ol>
    ),
    li: ({ children }) => <li className="leading-relaxed">{children}</li>,

    // Links
    a: ({ href, children }) => (
        <a
            href={href}
            className="text-sky-600 hover:text-sky-700 underline decoration-sky-200 hover:decoration-sky-400 transition-colors"
            target={href?.startsWith("http") ? "_blank" : undefined}
            rel={href?.startsWith("http") ? "noopener noreferrer" : undefined}
        >
            {children}
        </a>
    ),

    // Code
    code: ({ children }) => (
        <code className="px-1.5 py-0.5 bg-slate-100 text-pink-600 rounded text-sm font-mono">
            {children}
        </code>
    ),
    pre: ({ children }) => (
        <pre className="!bg-slate-900 !rounded-xl p-4 overflow-x-auto mb-6 shadow-lg">
            {children}
        </pre>
    ),

    // Blockquote
    blockquote: ({ children }) => (
        <blockquote className="border-l-4 border-sky-400 pl-4 py-2 my-4 bg-sky-50/50 rounded-r-lg italic text-slate-600">
            {children}
        </blockquote>
    ),

    // Horizontal Rule
    hr: () => <hr className="my-8 border-slate-200" />,

    // Strong and Emphasis
    strong: ({ children }) => (
        <strong className="font-semibold text-slate-800">{children}</strong>
    ),
    em: ({ children }) => <em className="italic">{children}</em>,

    // Tables
    table: ({ children }) => (
        <div className="overflow-x-auto mb-6">
            <table className="min-w-full divide-y divide-slate-200 border border-slate-200 rounded-lg">
                {children}
            </table>
        </div>
    ),
    thead: ({ children }) => <thead className="bg-slate-50">{children}</thead>,
    tbody: ({ children }) => (
        <tbody className="divide-y divide-slate-200">{children}</tbody>
    ),
    tr: ({ children }) => <tr>{children}</tr>,
    th: ({ children }) => (
        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
            {children}
        </th>
    ),
    td: ({ children }) => (
        <td className="px-4 py-3 text-sm text-slate-600">{children}</td>
    ),

    // Images
    img: ({ src, alt }) => (
        <figure className="my-6">
            <img
                src={src}
                alt={alt || ""}
                className="rounded-xl shadow-lg w-full"
            />
            {alt && (
                <figcaption className="text-center text-sm text-slate-500 mt-2">
                    {alt}
                </figcaption>
            )}
        </figure>
    ),

    // Custom Components
    Callout: ({ type = "info", children }: { type?: "info" | "warning" | "tip" | "danger"; children: React.ReactNode }) => {
        const styles = {
            info: { bg: "bg-sky-50", border: "border-sky-200", icon: <Info className="w-5 h-5 text-sky-600" /> },
            warning: { bg: "bg-amber-50", border: "border-amber-200", icon: <AlertTriangle className="w-5 h-5 text-amber-600" /> },
            tip: { bg: "bg-green-50", border: "border-green-200", icon: <Lightbulb className="w-5 h-5 text-green-600" /> },
            danger: { bg: "bg-red-50", border: "border-red-200", icon: <AlertCircle className="w-5 h-5 text-red-600" /> },
        };
        const style = styles[type];
        return (
            <div className={`flex gap-3 p-4 rounded-xl ${style.bg} border ${style.border} my-4`}>
                <div className="flex-shrink-0 mt-0.5">{style.icon}</div>
                <div className="text-sm">{children}</div>
            </div>
        );
    },
};

export default MDXComponents;
