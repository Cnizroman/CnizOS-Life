import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/api/client"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useState } from "react"

export default function Planner(){
  const [view,setView]=useState<string>("all")
  const [q,setQ]=useState("")
  const [show,setShow]=useState(false)
  const [form,setForm]=useState({title:"",priority:"medium",due_date:"",project_id:"",status:"todo"})
  const qc=useQueryClient()
  const {data, isLoading, error}=useQuery({queryKey:["tasks",view,q], queryFn:()=>api.get<any>(`/tasks?view=${view!=='all'?view:''}&q=${encodeURIComponent(q)}`)})
  const {data:projects}=useQuery({queryKey:["projects-mini"], queryFn:()=>api.get<any>("/projects?limit=100")})
  const create=useMutation({
    mutationFn:()=>api.post<any>("/tasks",{title:form.title,priority:form.priority,due_date: form.due_date ? new Date(form.due_date).toISOString() : undefined, project_id: form.project_id || undefined, status:form.status}),
    onSuccess:()=>{setShow(false); setForm({title:"",priority:"medium",due_date:"",project_id:"",status:"todo"}); qc.invalidateQueries({queryKey:["tasks"]})}
  })
  const update=useMutation({
    mutationFn:({id,status}:{id:string,status:string})=>api.patch<any>(`/tasks/${id}`,{status}),
    onSuccess:()=>qc.invalidateQueries({queryKey:["tasks"]})
  })
  const del=useMutation({
    mutationFn:(id:string)=>api.del(`/tasks/${id}`),
    onSuccess:()=>qc.invalidateQueries({queryKey:["tasks"]})
  })
  if(isLoading) return <div className="text-zinc-500">Загрузка...</div>
  if(error) return <div className="text-amber-200 bg-amber-950/30 border border-amber-900 rounded-xl p-4">{(error as Error).message}</div>
  const list = data?.data || []
  const today = new Date().toISOString().slice(0,10)
  return (
    <div className="space-y-4 pb-20">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <h1 className="text-2xl font-semibold">Planner</h1>
        <Button onClick={()=>setShow(!show)}>+ Задача</Button>
      </div>
      <div className="flex flex-wrap gap-2">
        <Input placeholder="Поиск задач..." value={q} onChange={e=>setQ(e.target.value)} className="max-w-[240px]" />
        <select value={view} onChange={e=>setView(e.target.value)} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm">
          <option value="all">Все</option><option value="today">Сегодня</option><option value="overdue">Просроченные</option><option value="upcoming">Ближайшие 7д</option><option value="done">Выполненные</option>
        </select>
      </div>
      {show && (
        <Card className="border-[#4ADE80]/30">
          <CardHeader><CardTitle className="text-base">Новая задача</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="Название *" value={form.title} onChange={e=>setForm({...form,title:e.target.value})} />
            <div className="grid grid-cols-2 gap-3">
              <select value={form.priority} onChange={e=>setForm({...form,priority:e.target.value})} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm"><option value="low">low</option><option value="medium">medium</option><option value="high">high</option><option value="urgent">urgent</option></select>
              <select value={form.status} onChange={e=>setForm({...form,status:e.target.value})} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm"><option value="todo">todo</option><option value="in_progress">in_progress</option><option value="done">done</option></select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Input type="datetime-local" value={form.due_date} onChange={e=>setForm({...form,due_date:e.target.value})} />
              <select value={form.project_id} onChange={e=>setForm({...form,project_id:e.target.value})} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm">
                <option value="">Без проекта</option>{projects?.data?.map((p:any)=><option key={p.id} value={p.id}>{p.title}</option>)}
              </select>
            </div>
            <div className="flex gap-2">
              <Button onClick={()=>create.mutate()} disabled={!form.title.trim()}>Создать</Button>
              <Button variant="outline" onClick={()=>setShow(false)}>Отмена</Button>
            </div>
          </CardContent>
        </Card>
      )}
      <div className="grid md:grid-cols-3 gap-3">
        <Card><CardContent className="pt-4"><div className="text-xs text-zinc-500">Сегодня</div><div className="text-xl font-bold">{list.filter((t:any)=> t.due_date && t.due_date.slice(0,10)===today).length}</div></CardContent></Card>
        <Card><CardContent className="pt-4"><div className="text-xs text-zinc-500">Просрочено</div><div className="text-xl font-bold text-amber-500">{list.filter((t:any)=> t.due_date && new Date(t.due_date) < new Date() && t.status!=="done").length}</div></CardContent></Card>
        <Card><CardContent className="pt-4"><div className="text-xs text-zinc-500">Выполнено</div><div className="text-xl font-bold text-emerald-500">{list.filter((t:any)=>t.status==="done").length}</div></CardContent></Card>
      </div>
      <div className="space-y-2">
        {list.length===0 ? <Card><CardContent className="p-8 text-center text-zinc-500">Нет задач. Создай первую — с дедлайном, проектом и напоминанием.<br/><span className="text-xs">POST /api/v1/tasks</span></CardContent></Card> :
          list.map((t:any)=>(
            <Card key={t.id} className="hover:border-zinc-700">
              <CardContent className="p-4 flex items-start gap-3">
                <button onClick={()=>update.mutate({id:t.id,status: t.status==="done"?"todo":"done"})} className={`w-5 h-5 rounded-full border mt-0.5 shrink-0 flex items-center justify-center ${t.status==="done"?"bg-[#4ADE80] border-[#4ADE80]":"border-zinc-600"}`}>{t.status==="done"&&"✓"}</button>
                <div className="flex-1 min-w-0">
                  <div className={`font-medium ${t.status==="done"?"line-through text-zinc-500":""}`}>{t.title}</div>
                  <div className="flex flex-wrap gap-2 mt-1">
                    <Badge variant="outline" className="text-[10px]">{t.priority}</Badge>
                    <Badge variant="secondary" className="text-[10px]">{t.status}</Badge>
                    {t.due_date && <span className="text-xs text-zinc-500">до {new Date(t.due_date).toLocaleString("ru-RU")}</span>}
                    {t.project_id && <span className="text-xs text-zinc-500">проект: {projects?.data?.find((p:any)=>p.id===t.project_id)?.title || t.project_id.slice(0,6)}</span>}
                  </div>
                </div>
                <div className="flex gap-1 shrink-0">
                  <select value={t.status} onChange={e=>update.mutate({id:t.id,status:e.target.value})} className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs">
                    <option value="todo">todo</option><option value="in_progress">in_progress</option><option value="done">done</option><option value="cancelled">cancelled</option>
                  </select>
                  <Button variant="ghost" size="sm" onClick={()=>del.mutate(t.id)}>✕</Button>
                </div>
              </CardContent>
            </Card>
          ))
        }
      </div>
      <Card className="border-dashed"><CardContent className="p-4 text-xs text-zinc-500">Календарь: <code>GET /api/v1/tasks/calendar?from=...&to=...</code> — подключится в виджете Dashboard. Повторяющиеся задачи — поле recurrence_rule (RRULE).</CardContent></Card>
    </div>
  )
}
