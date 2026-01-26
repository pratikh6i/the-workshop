import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import CommandPalette from "@/components/CommandPalette";
import { getAllDays, getProgress } from "@/lib/content";

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
  authors: [{ name: "Pratik Shetti", url: "https://www.linkedin.com/in/pratikshetti/" }],
  keywords: ["cybersecurity", "security", "cloud security", "GCP", "linux", "workshops"],
  metadataBase: new URL("https://pratikh6i.github.io"),
  openGraph: {
    title: "The Workshop | 90-Day Security Odyssey",
    description: "A comprehensive 90-day journey through cybersecurity",
    type: "website",
  },
  robots: {
    index: true,
    follow: true,
  },
  viewport: {
    width: "device-width",
    initialScale: 1,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Fetch data at build time (server component)
  const allDays = getAllDays();
  const progress = getProgress();

  const sidebarDays = allDays.map(d => ({
    slug: d.slug,
    dayNumber: d.dayNumber,
    title: d.title,
    status: d.status
  }));

  const searchItems = allDays.map(d => ({
    slug: d.slug,
    dayNumber: d.dayNumber,
    title: d.title,
    description: d.description || "",
    content: d.content || "",
  }));

  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`} suppressHydrationWarning>
      <body suppressHydrationWarning>
        <div className="app-container">
          {/* Fixed Sidebar */}
          <div className="sidebar-wrapper">
            <Sidebar days={sidebarDays} progress={progress} />
          </div>

          {/* Main Content Area */}
          <div className="main-wrapper">
            {/* Fixed Header */}
            <div className="header-wrapper">
              <Header />
            </div>

            {/* Page Content */}
            <div className="content-wrapper">
              {children}
            </div>

            {/* Footer */}
            <Footer />
          </div>
        </div>

        {/* Command Palette (Global) */}
        <CommandPalette items={searchItems} />
      </body>
    </html>
  );
}
