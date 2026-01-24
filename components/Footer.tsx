"use client";

import { Linkedin, Twitter } from "lucide-react";

export default function Footer() {
    return (
        <footer className="footer">
            <div className="footer-content">
                <div className="footer-right">
                    <p className="footer-text">
                        Made with Love &amp; Prompts with <span className="footer-highlight">Antigravity 💜</span>
                    </p>
                    <div className="footer-social">
                        <a
                            href="https://www.linkedin.com/in/pratikshetti/"
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label="LinkedIn Profile"
                            className="footer-link"
                        >
                            <Linkedin className="footer-icon" />
                        </a>
                        <a
                            href="https://x.com/pratik_h6i"
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label="Twitter Profile"
                            className="footer-link"
                        >
                            <Twitter className="footer-icon" />
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    );
}
