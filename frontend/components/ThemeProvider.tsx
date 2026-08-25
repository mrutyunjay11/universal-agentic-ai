"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

type Theme = "dark" | "light";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: "dark",
  setTheme: () => {},
  toggleTheme: () => {},
});

export function useTheme() {
  return useContext(ThemeContext);
}

interface ThemeProviderProps {
  children: ReactNode;
  attribute?: string;
  defaultTheme?: Theme;
  enableSystem?: boolean;
  storageKey?: string;
}

export function ThemeProvider({
  children,
  attribute = "class",
  defaultTheme = "dark",
  storageKey = "lca-theme",
}: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(defaultTheme);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem(storageKey) as Theme | null;
    if (stored === "dark" || stored === "light") {
      setThemeState(stored);
    }
  }, [storageKey]);

  useEffect(() => {
    if (!mounted) return;
    const root = document.documentElement;
    if (attribute === "class") {
      root.classList.remove("dark", "light");
      root.classList.add(theme);
    } else {
      root.setAttribute(attribute, theme);
    }
    localStorage.setItem(storageKey, theme);
  }, [theme, mounted, attribute, storageKey]);

  const setTheme = (t: Theme) => setThemeState(t);
  const toggleTheme = () => setThemeState((prev) => (prev === "dark" ? "light" : "dark"));

  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
