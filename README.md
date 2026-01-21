# The Workshop 🛡️

> A 90-Day Security Odyssey — A documentation app for your cybersecurity learning journey.

![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?style=flat-square&logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-38bdf8?style=flat-square&logo=tailwindcss)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## ✨ Features

- **Psychological UX Design** - Smart reverse chronological feed with current day pinned at top
- **Metro Line Sidebar** - Visual progress tracker that fills upward as you complete days
- **Command-K Search** - Fuzzy search with `⌘K` keyboard shortcut
- **MDX Content** - Write in Markdown with React components
- **Glassmorphism UI** - Premium "Faint Fresh" aesthetic
- **Static Export** - Deploys to GitHub Pages
- **Day Generator** - CLI script to create new day entries

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/pratikh6i/the-workshop.git
cd the-workshop

# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see your app.

## 📝 Creating New Days

Use the built-in generator script:

```bash
node scripts/new-day.js 4 "Authentication Basics"
```

This creates `content/day-04-authentication-basics/index.mdx` with:
- Auto-calculated date
- Frontmatter template
- Starter content structure

## 📁 Project Structure

```
the-workshop/
├── app/
│   ├── layout.tsx         # Root layout with fonts
│   ├── page.tsx           # Main feed page
│   └── day/[slug]/        # Day detail pages
├── components/
│   ├── Sidebar.tsx        # Metro Line tracker
│   ├── Header.tsx         # Glassmorphic header
│   ├── CommandPalette.tsx # CMD+K search
│   ├── CurrentDay.tsx     # Active day hero
│   └── DayCard.tsx        # Feed cards
├── content/
│   └── day-XX-slug/       # MDX content folders
├── lib/
│   ├── content.ts         # Content utilities
│   └── types.ts           # TypeScript types
└── scripts/
    └── new-day.js         # Day generator
```

## 🎨 Design System

- **Background**: Porcelain (`#f8fafc`)
- **Accents**: Mint, Sky, Coral pastels
- **Typography**: Inter (UI), JetBrains Mono (code)
- **Effects**: Glassmorphism with `backdrop-blur-xl`

## 🌐 Deployment

Automatic deployment to GitHub Pages on push to `main`:

1. Push your changes to `main`
2. GitHub Actions builds the static site
3. Deploys to `gh-pages` branch
4. Live at `https://pratikh6i.github.io/the-workshop/`

## 📄 License

MIT © 2026
