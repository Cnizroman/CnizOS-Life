import { create } from "zustand"

type Theme = "dark" | "light"
type Density = "comfortable" | "compact"

type ThemeState = {
  theme: Theme
  accent: string
  density: Density
  sidebarCollapsed: boolean
  setTheme: (t: Theme) => void
  setAccent: (c: string) => void
  setDensity: (d: Density) => void
  toggleSidebar: () => void
}

export const useTheme = create<ThemeState>((set) => ({
  theme: (localStorage.getItem("cnizos_theme") as Theme) || "dark",
  accent: localStorage.getItem("cnizos_accent") || "#4ADE80",
  density: (localStorage.getItem("cnizos_density") as Density) || "comfortable",
  sidebarCollapsed: localStorage.getItem("cnizos_sidebar") === "collapsed",
  setTheme: (theme) => {
    localStorage.setItem("cnizos_theme", theme)
    document.documentElement.classList.toggle("light", theme === "light")
    set({ theme })
  },
  setAccent: (accent) => {
    localStorage.setItem("cnizos_accent", accent)
    set({ accent })
  },
  setDensity: (density) => {
    localStorage.setItem("cnizos_density", density)
    set({ density })
  },
  toggleSidebar: () => set((s) => {
    const v = !s.sidebarCollapsed
    localStorage.setItem("cnizos_sidebar", v ? "collapsed" : "expanded")
    return { sidebarCollapsed: v }
  }),
}))
