import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import CommandPalette from "@/components/CommandPalette";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  title: "The Workshop | 90-Day Security Odyssey",
  description: "A comprehensive 90-day journey through cybersecurity, documenting daily learnings, challenges, and discoveries.",
  keywords: ["security", "cybersecurity", "learning", "documentation", "90 days"],
  authors: [{ name: "Security Enthusiast" }],
  openGraph: {
    title: "The Workshop | 90-Day Security Odyssey",
    description: "A comprehensive 90-day journey through cybersecurity",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="antialiased">
        <div className="flex min-h-screen">
          {/* Sidebar */}
          <Sidebar />

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col ml-0 lg:ml-[280px]">
            {/* Header */}
            <Header />

            {/* Page Content */}
            <main className="flex-1 pt-[80px] px-4 lg:px-8 pb-12">
              <div className="max-w-4xl mx-auto">
                {children}
              </div>
            </main>
          </div>
        </div>

        {/* Command Palette (Global) */}
        <CommandPalette />
      </body>
    </html>
  );
}
