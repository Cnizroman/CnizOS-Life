import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/api/client"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Clock, CheckCircle2, AlertTriangle, Calendar, Rocket, FileText, Link2, Bot, Monitor, ListTodo, Bell } from "lucide-react"
import { useState } from "react"

function useSummary() {
  return useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => api.get<any>("/dashboard/summary"),
    retry: false,
  })
}

export default function Dashboard() {
  const { data, isLoading, error } = useSummary()
  const qc = useQueryClient()
  const [quick, setQuick] = useState("")
  const [quickType, setQuickType] = useState<"task"|"note"|"project">("task")

  const createQuick = useMutation({
    mutationFn: () => {
      if (quickType==="task") return api.post("/tasks", { title: quick })
      if (quickType==="note") return api.post("/notes", { title: quick, body: quick, type: "note" })
      return api.post("/projects", { title: quick, category: "other" })
    },
    onSuccess: () => { setQuick(""); qc.invalidateQueries({queryKey:["dashboard-summary"]}) }
  })

  const now = new Date()
  const time = now.toLocaleTimeString("ru-RU", { hour:"2-digit", minute:"2-digit" })
  const date = now.toLocaleDateString("ru-RU", { weekday:"long", day:"numeric", month:"long" })

  if (isLoading) return <div className="text-zinc-500">Загрузка дашборда...</div>
  if (error) return <div className="rounded-2xl border border-amber-900 bg-amber-950/30 p-6 text-amber-200">Backend недоступен — проверь <code>docker compose up</code>. Ошибка: {(error as Error).message}</div>

  const s = data || { today_tasks:0, overdue_tasks:0, active_projects:0, recent_notes:[], bridge_status:"offline", upcoming_deadlines:[], reminders:[] }

  return (
    <div className="space-y-6 pb-20">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1><p className="text-sm text-zinc-500">Твой персональный центр — {date}</p></div>
        <div className="flex gap-2">
          <select value={quickType} onChange={e=>setQuickType(e.target.value as any)} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 text-sm">
            <option value="task">Задача</option><option value="note">Заметка</option><option value="project">Проект</option>
          </select>
          <Input placeholder="Быстро создать..." value={quick} onChange={e=>setQuick(e.target.value)} className="w-[200px]" />
          <Button onClick={()=>createQuick.mutate()} disabled={!quick.trim() || createQuick.isPending}>+ Создать</Button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* Clock */}
        <Card className="col-span-12 md:col-span-4">
          <CardHeader className="pb-2"><div className="flex items-center gap-2 text-xs tracking-widest text-zinc-500"><Clock size={14}/> CLOCK <Badge variant="outline" className="ml-auto text-[10px]">LOCAL TIME</Badge></div></CardHeader>
          <CardContent>
            <div className="text-5xl font-light tracking-tight">{time}<span className="text-lg ml-1">AM</span></div>
            <div className="text-zinc-400 capitalize mt-1">{date}</div>
            <div className="text-xs text-zinc-500 mt-2">Tallinn • {Intl.DateTimeFormat().resolvedOptions().timeZone}</div>
          </CardContent>
        </Card>

        {/* Today tasks */}
        <Card className="col-span-12 md:col-span-4">
          <CardHeader className="pb-2"><div className="flex items-center justify-between"><span className="text-xs tracking-widest text-zinc-500 flex items-center gap-2"><ListTodo size={14}/> TODAY — TASKS</span><span className="text-xs text-zinc-500">{s.today_tasks} задач</span></div></CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm"><CheckCircle2 size={16} className="text-emerald-500"/><span className="line-through text-zinc-500">Пример — подключи backend для реальных задач</span></div>
              <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden mt-3"><div className="h-full bg-[#4ADE80] w-[60%]" /></div>
              <div className="text-xs text-zinc-500 flex justify-between"><span>{s.overdue_tasks} просрочено</span><span>{s.today_tasks} всего</span></div>
            </div>
          </CardContent>
        </Card>

        {/* Bridge */}
        <Card className="col-span-12 md:col-span-4">
          <CardHeader className="pb-2"><div className="flex items-center gap-2 text-xs tracking-widest text-zinc-500"><Monitor size={14}/> BRIDGE STATUS <Badge variant={s.bridge_status==="online" ? "default" : "secondary"} className="ml-auto">{s.bridge_status}</Badge></div></CardHeader>
          <CardContent>
            <div className="text-lg font-medium">{s.bridge_status==="online" ? "All Systems Normal" : "Bridge offline"}</div>
            <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
              <div><div className="text-zinc-500 text-xs">UPTIME</div><div>—</div></div>
              <div><div className="text-zinc-500 text-xs">LAST CHECK</div><div>{new Date().toLocaleTimeString()}</div></div>
            </div>
            <div className="mt-3 text-xs text-zinc-500">{s.bridge_status==="online" ? "Команды выполняются" : "Включи Bridge на Windows: CnizOS-Bridge.exe"}</div>
          </CardContent>
        </Card>

        {/* Active projects */}
        <Card className="col-span-12 lg:col-span-8">
          <CardHeader><div className="flex items-center justify-between"><span className="text-xs tracking-widest text-zinc-500 flex items-center gap-2"><Rocket size={14}/> ACTIVE PROJECTS</span><span className="text-xs text-zinc-500">{s.active_projects} проектов</span></div></CardHeader>
          <CardContent>
            {s.active_projects===0 ? (
              <div className="rounded-xl border border-dashed border-zinc-700 p-8 text-center">
                <div className="text-zinc-400 mb-2">Нет активных проектов</div>
                <p className="text-sm text-zinc-500 mb-4">Создай первый проект — он появится здесь и в виджетах</p>
                <Button variant="outline" onClick={()=>window.location.href="/projects"}>+ Создать проект</Button>
              </div>
            ) : (
              <div className="grid md:grid-cols-3 gap-3">
                {[1,2,3].slice(0, s.active_projects).map(i=>(
                  <div key={i} className="rounded-xl border border-zinc-800 p-4 bg-zinc-900/30">
                    <div className="text-xs text-zinc-500">PROJECT {i}</div><div className="font-medium mt-1">Пример проекта</div>
                    <div className="h-1.5 bg-zinc-800 rounded-full mt-3"><div className="h-full bg-[#4ADE80]" style={{width:`${30+i*20}%`}} /></div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent notes */}
        <Card className="col-span-12 lg:col-span-4">
          <CardHeader><div className="flex items-center gap-2 text-xs tracking-widest text-zinc-500"><FileText size={14}/> RECENT NOTES</div></CardHeader>
          <CardContent>
            {s.recent_notes?.length ? s.recent_notes.map((n:any)=>(
              <div key={n.id} className="py-2 border-b border-zinc-800 last:border-0">
                <div className="text-sm font-medium truncate">{n.title}</div><div className="text-xs text-zinc-500 truncate">{n.snippet}</div>
              </div>
            )) : (
              <div className="text-sm text-zinc-500 py-4">Пока нет заметок. <span className="text-[#4ADE80]">+ Новая заметка</span> создаст первую.</div>
            )}
          </CardContent>
        </Card>

        {/* Quick stats row */}
        <div className="col-span-12 grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card><CardContent className="pt-5"><div className="flex items-center gap-2 text-xs text-zinc-500"><AlertTriangle size={14}/> ПРОСРОЧЕНО</div><div className="text-2xl font-semibold mt-1">{s.overdue_tasks}</div></CardContent></Card>
          <Card><CardContent className="pt-5"><div className="flex items-center gap-2 text-xs text-zinc-500"><Calendar size={14}/> ДЕДЛАЙНЫ</div><div className="text-2xl font-semibold mt-1">{s.upcoming_deadlines?.length || 0}</div></CardContent></Card>
          <Card><CardContent className="pt-5"><div className="flex items-center gap-2 text-xs text-zinc-500"><Bot size={14}/> ZORO</div><div className="text-sm mt-1 text-zinc-400">Готов к командам</div></CardContent></Card>
          <Card><CardContent className="pt-5"><div className="flex items-center gap-2 text-xs text-zinc-500"><Bell size={14}/> НАПОМИНАНИЯ</div><div className="text-2xl font-semibold mt-1">{s.reminders?.length || 0}</div></CardContent></Card>
        </div>
      </div>

      <div className="flex items-center gap-2 text-xs text-zinc-600 border-t border-zinc-800 pt-4">
        <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" /> All data synced • Just now <span className="ml-auto">Personal Dashboard • v2 — Этап 2</span>
      </div>
    </div>
  )
}
