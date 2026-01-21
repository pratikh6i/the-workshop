#!/usr/bin/env node

/**
 * new-day.js - Generate boilerplate for a new day entry
 * 
 * Usage:
 *   node scripts/new-day.js <day-number> "<title>"
 * 
 * Example:
 *   node scripts/new-day.js 4 "Authentication Basics"
 * 
 * This will create:
 *   content/day-04-authentication-basics/index.mdx
 */

const fs = require("fs");
const path = require("path");

// ANSI color codes for terminal output
const colors = {
    reset: "\x1b[0m",
    bright: "\x1b[1m",
    green: "\x1b[32m",
    yellow: "\x1b[33m",
    blue: "\x1b[34m",
    cyan: "\x1b[36m",
    red: "\x1b[31m",
};

function log(message, color = "reset") {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function slugify(text) {
    return text
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "");
}

function getStartDate() {
    // Default start date - adjust this to your actual start date
    return new Date("2026-01-19");
}

function calculateDate(dayNumber) {
    const startDate = getStartDate();
    const date = new Date(startDate);
    date.setDate(date.getDate() + dayNumber - 1);
    return date.toISOString().split("T")[0];
}

function generateFrontmatter(dayNumber, title, slug) {
    const date = calculateDate(dayNumber);

    return `---
title: "${title}"
description: "Day ${dayNumber} of the 90-Day Security Odyssey. Add your description here."
date: "${date}"
status: "draft"
difficulty: "beginner"
tags: []
---

# ${title}

Welcome to **Day ${dayNumber}** of the 90-Day Security Odyssey.

## Overview

Add your overview content here.

## Key Concepts

- Concept 1
- Concept 2
- Concept 3

## Hands-On Exercise

\`\`\`bash
# Add your code examples here
echo "Day ${dayNumber}: ${title}"
\`\`\`

## Key Takeaways

- Takeaway 1
- Takeaway 2
- Takeaway 3

---

**Tomorrow:** Preview of the next topic.
`;
}

function createDay(dayNumber, title) {
    const slug = slugify(title);
    const folderName = `day-${dayNumber.toString().padStart(2, "0")}-${slug}`;
    const contentDir = path.join(process.cwd(), "content");
    const folderPath = path.join(contentDir, folderName);
    const filePath = path.join(folderPath, "index.mdx");

    // Check if content directory exists
    if (!fs.existsSync(contentDir)) {
        fs.mkdirSync(contentDir, { recursive: true });
        log(`✓ Created content directory`, "green");
    }

    // Check if folder already exists
    if (fs.existsSync(folderPath)) {
        log(`✗ Error: ${folderName} already exists!`, "red");
        process.exit(1);
    }

    // Create folder
    fs.mkdirSync(folderPath, { recursive: true });

    // Generate and write content
    const content = generateFrontmatter(dayNumber, title, slug);
    fs.writeFileSync(filePath, content, "utf8");

    log("", "reset");
    log("╔════════════════════════════════════════════════════════╗", "cyan");
    log("║           🚀 New Day Created Successfully! 🚀          ║", "cyan");
    log("╚════════════════════════════════════════════════════════╝", "cyan");
    log("", "reset");
    log(`  📁 Folder:  ${folderName}`, "blue");
    log(`  📄 File:    ${filePath}`, "blue");
    log(`  📅 Date:    ${calculateDate(dayNumber)}`, "blue");
    log("", "reset");
    log("  Next steps:", "yellow");
    log("  1. Edit the MDX file to add your content", "reset");
    log("  2. Update the 'status' to 'in-progress' when you start", "reset");
    log("  3. Change 'status' to 'completed' when done", "reset");
    log("", "reset");
}

// Main execution
const args = process.argv.slice(2);

if (args.length < 2) {
    log("", "reset");
    log("📘 New Day Generator for The Workshop", "bright");
    log("", "reset");
    log("Usage:", "yellow");
    log("  node scripts/new-day.js <day-number> \"<title>\"", "reset");
    log("", "reset");
    log("Example:", "yellow");
    log("  node scripts/new-day.js 4 \"Authentication Basics\"", "reset");
    log("", "reset");
    process.exit(1);
}

const dayNumber = parseInt(args[0], 10);
const title = args.slice(1).join(" ").replace(/^["']|["']$/g, "");

if (isNaN(dayNumber) || dayNumber < 1 || dayNumber > 90) {
    log("✗ Error: Day number must be between 1 and 90", "red");
    process.exit(1);
}

if (!title || title.trim().length === 0) {
    log("✗ Error: Title is required", "red");
    process.exit(1);
}

createDay(dayNumber, title.trim());
