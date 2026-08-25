import type { Metadata } from "next";
import { ThemeProvider } from "@/components/ThemeProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Universal Agentic AI — Autonomous Multi-Agent & Dynamic Context Intelligence",
  description: "Universal Agentic AI platform powered by Qwen3.8-Max, Dynamic Context Intelligence, Multi-Agent Orchestration, and Verified Tools.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          storageKey="lca-theme"
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
