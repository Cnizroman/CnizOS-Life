import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import AppShell from "@/layouts/AppShell"
import Dashboard from "@/modules/dashboard/Dashboard"
import Projects from "@/modules/projects/Projects"
import ProjectDetail from "@/modules/projects/ProjectDetail"
import Planner from "@/modules/planner/Planner"
import Memory from "@/modules/memory/Memory"
import NoteDetail from "@/modules/memory/NoteDetail"
import Creative from "@/modules/creative/Creative"
import ZoroHub from "@/modules/zoro/ZoroHub"
import PcControl from "@/modules/pc-control/PcControl"
import Automation from "@/modules/automation/Automation"
import Settings from "@/modules/settings/Settings"
import SearchPage from "@/modules/search/Search"
import Setup from "@/pages/auth/Setup"
import Login from "@/pages/auth/Login"
import { useAuth } from "@/stores/auth"
import { api } from "@/api/client"

const qc = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false } }
})

function Protected({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  const [checking, setChecking] = useState(true)
  const [needsSetup, setNeedsSetup] = useState<boolean | null>(null)
  const auth = useAuth()

  useEffect(() => {
    api.get<{setup_required: boolean}>("/auth/setup-status").then((r)=>{
      setNeedsSetup(r.setup_required)
      auth.setSetupRequired(r.setup_required)
    }).catch(()=>{
      setNeedsSetup(false)
    }).finally(()=>setChecking(false))
  }, [])

  if (checking) return <div className="min-h-screen flex items-center justify-center bg-[#0A0A0B] text-zinc-500">Загрузка CnizOS...</div>
  if (needsSetup) return <Navigate to="/setup" replace />
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  useEffect(()=>{
    const t = localStorage.getItem("cnizos_theme") || "dark"
    document.documentElement.classList.toggle("light", t==="light")
    // PWA install prompt
    if ('serviceWorker' in navigator) {
      // simple sw registration for offline shell
      // will be generated in production build
    }
  },[])
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Routes>
          <Route path="/setup" element={<Setup/>} />
          <Route path="/login" element={<Login/>} />
          <Route element={<Protected><AppShell/></Protected>}>
            <Route path="/" element={<Dashboard/>} />
            <Route path="/projects" element={<Projects/>} />
            <Route path="/projects/:id" element={<ProjectDetail/>} />
            <Route path="/planner" element={<Planner/>} />
            <Route path="/memory" element={<Memory/>} />
            <Route path="/memory/:id" element={<NoteDetail/>} />
            <Route path="/creative" element={<Creative/>} />
            <Route path="/zoro" element={<ZoroHub/>} />
            <Route path="/pc" element={<PcControl/>} />
            <Route path="/automation" element={<Automation/>} />
            <Route path="/settings" element={<Settings/>} />
            <Route path="/search" element={<SearchPage/>} />
          </Route>
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
