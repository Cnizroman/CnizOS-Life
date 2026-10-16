import { useState, useEffect } from "react"
import { NavLink, Outlet, useNavigate } from "react-router-dom"
import { LayoutDashboard, FolderKanban, CalendarCheck, Brain, Palette, Bot, MonitorSmartphone, Zap, Settings, Search, Command, Menu, X, LogOut, PanelLeftClose, PanelLeftOpen } from "lucide-react"
import { useAuth } from "@/stores/auth"
import { useTheme } from "@/stores/theme"
import { useBridgeStatus } from "@/hooks/useBridgeStatus"
import { api } from "@/api/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

const nav = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/projects", icon: FolderKanban, label: "Projects" },
  { to: "/planner", icon: CalendarCheck, label: "Planner" },
  { to: "/memory", icon: Brain, label: "Memory" },
  { to: "/creative", icon: Palette, label: "Creative" },
  { to: "/zoro", icon: Bot, label: "Zoro Hub" },
  { to: "/pc", icon: MonitorSmartphone, label: "PC Control" },
  { to: "/automation", icon: Zap, label: "Automation" },
  { to: "/settings", icon: Settings, label: "Settings" },
]

export default function AppShell() {
  const { user, logout } = useAuth()
  const { sidebarCollapsed, toggleSidebar } = useTheme()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [search, setSearch] = useState("")
  const navigate = useNavigate()
  const bridge = useBridgeStatus()

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        document.getElementById("global-search")?.focus()
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!search.trim()) return
    navigate(`/search?q=${encodeURIComponent(search)}`)
  }

  const handleLogout = async () => {
    try { await api.post("/auth/logout") } catch {}
    logout()
    navigate("/login")
  }

  const bridgeOnline = bridge.data?.connected
  const bridgeCount = bridge.data?.devices?.length || 0

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-zinc-100 flex">
      {/* Desktop sidebar */}
      <aside className={`hidden md:flex flex-col border-r border-zinc-800 bg-[#0F0F10] transition-all ${sidebarCollapsed ? "w-[64px]" : "w-[240px]"} shrink-0 sticky top-0 h-screen`}>
        <div className="h-[64px] flex items-center px-4 gap-3 border-b border-zinc-800">
          <div className="w-8 h-8 rounded-lg bg-[#4ADE80] flex items-center justify-center font-bold text-black text-sm shrink-0">C</div>
          {!sidebarCollapsed && <span className="font-semibold tracking-tight">CnizOS</span>}
          <button onClick={toggleSidebar} className="ml-auto p-1.5 rounded-lg hover:bg-zinc-800 text-zinc-400">
            {sidebarCollapsed ? <PanelLeftOpen size={16}/> : <PanelLeftClose size={16}/>}
          </button>
        </div>
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {nav.map(i => (
            <NavLink key={i.to} to={i.to} end={i.to==="/"} className={({isActive})=>`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors ${isActive ? "bg-[#4ADE80] text-black font-medium" : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"}`}>
              <i.icon size={18} className="shrink-0" />
              {!sidebarCollapsed && <span>{i.label}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-zinc-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center text-sm font-medium shrink-0">{user?.display_name?.[0] || "U"}</div>
            {!sidebarCollapsed && (
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{user?.display_name || "Owner"}</div>
                <div className="text-xs text-zinc-500 truncate">{user?.email}</div>
              </div>
            )}
            {!sidebarCollapsed && <button onClick={handleLogout} className="p-1.5 hover:bg-zinc-800 rounded-lg text-zinc-500"><LogOut size={14}/></button>}
          </div>
        </div>
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={()=>setMobileOpen(false)} />
          <div className="absolute left-0 top-0 bottom-0 w-[280px] bg-[#0F0F10] border-r border-zinc-800 p-4 flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2"><div className="w-8 h-8 rounded-lg bg-[#4ADE80] flex items-center justify-center font-bold text-black">C</div><span className="font-semibold">CnizOS</span></div>
              <button onClick={()=>setMobileOpen(false)} className="p-2 hover:bg-zinc-800 rounded-lg"><X size={18}/></button>
            </div>
            <nav className="space-y-1 flex-1">
              {nav.map(i=>(
                <NavLink key={i.to} to={i.to} onClick={()=>setMobileOpen(false)} className={({isActive})=>`flex items-center gap-3 px-3 py-3 rounded-xl ${isActive ? "bg-[#4ADE80] text-black font-medium" : "text-zinc-400"}`}>
                  <i.icon size={18}/>{i.label}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      )}

      <div className="flex-1 min-w-0 flex flex-col">
        {/* Top bar */}
        <header className="h-[64px] border-b border-zinc-800 bg-[#0F0F10]/80 backdrop-blur sticky top-0 z-30 flex items-center gap-3 px-4">
          <button onClick={()=>setMobileOpen(true)} className="md:hidden p-2 hover:bg-zinc-800 rounded-xl"><Menu size={18}/></button>

          <form onSubmit={handleSearch} className="flex-1 max-w-[640px] relative hidden sm:flex">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <Input id="global-search" placeholder="Search or jump to...  ⌘K" value={search} onChange={e=>setSearch(e.target.value)} className="pl-9 bg-zinc-900 border-zinc-800 h-9" />
          </form>

          <div className="ml-auto flex items-center gap-2 sm:gap-3">
            <div className="hidden sm:flex items-center gap-2 text-xs">
              <span className={`w-2 h-2 rounded-full ${bridgeOnline ? "bg-emerald-500" : "bg-red-500"} animate-pulse`} />
              <span className={bridgeOnline ? "text-emerald-400" : "text-zinc-500"}>{bridgeOnline ? `Bridge online • ${bridgeCount}` : "Bridge offline"}</span>
            </div>
            <div className="w-px h-6 bg-zinc-800 hidden sm:block" />
            <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-xs font-medium">{user?.display_name?.[0] || "U"}</div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-4 md:p-6 bg-[#0A0A0B] min-w-0">
          <Outlet />
        </main>

        {/* Mobile bottom nav */}
        <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-[#0F0F10] border-t border-zinc-800 flex justify-around py-2 z-30">
          {nav.slice(0,5).map(i=>(
            <NavLink key={i.to} to={i.to} className={({isActive})=>`flex flex-col items-center gap-1 px-3 py-1 rounded-xl ${isActive ? "text-[#4ADE80]" : "text-zinc-500"}`}>
              <i.icon size={18}/><span className="text-[10px]">{i.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  )
}
