import { useParams, Link } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/api/client"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useState } from "react"

export default function ProjectDetail(){
  const {id}=useParams()
  const qc=useQueryClient()
  const {data:proj, isLoading, error}=useQuery({queryKey:["project",id], queryFn:()=>api.get<any>(`/projects/${id}`)})
  const {data:tasks}=useQuery({queryKey:["project-tasks",id], queryFn:()=>api.get<any>(`/projects/${id}/tasks`), enabled: !!id})
  const {data:notes}=useQuery({queryKey:["project-notes",id], queryFn:()=>api.get<any>(`/projects/${id}/notes`), enabled: !!id})
  const [nextStep,setNextStep]=useState("")
  const update=useMutation({
    mutationFn:(payload:any)=>api.patch<any>(`/projects/${id}`,payload),
    onSuccess:()=>qc.invalidateQueries({queryKey:["project",id]})
  })
  if(isLoading) return <div className="text-zinc-500">Загрузка...</div>
  if(error) return <div className="text-red-400">Ошибка: {(error as Error).message} <Link to="/projects" className="text-[#4ADE80]">← к списку</Link></div>
  if(!proj) return <div>Не найдено</div>
  return (
    <div className="space-y-6 pb-20">
      <Link to="/projects" className="text-sm text-zinc-500 hover:text-zinc-300">← Все проекты</Link>
      <div className="flex flex-wrap gap-3 items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{proj.title}</h1>
          <div className="flex gap-2 mt-2"><Badge>{proj.category}</Badge><Badge variant="secondary">{proj.status}</Badge><Badge variant="outline">{proj.priority}</Badge></div>
          {proj.description && <p className="text-zinc-400 mt-3 max-w-2xl">{proj.description}</p>}
          <div className="flex gap-3 mt-3 text-sm">
            {proj.github_url && <a href={proj.github_url} target="_blank" className="text-[#4ADE80] hover:underline">GitHub →</a>}
            {proj.demo_url && <a href={proj.demo_url} target="_blank" className="text-[#4ADE80] hover:underline">Demo →</a>}
            {proj.local_path && <span className="text-zinc-500">📁 {proj.local_path}</span>}
          </div>
        </div>
        <div className="flex gap-2">
          <select value={proj.status} onChange={e=>update.mutate({status:e.target.value})} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm">
            <option value="idea">idea</option><option value="active">active</option><option value="paused">paused</option><option value="done">done</option><option value="archived">archived</option>
          </select>
          <Button variant="outline" onClick={()=>{if(confirm("Архивировать?")) update.mutate({status:"archived"})}}>Архив</Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle className="text-base">Что сделано / Что осталось</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <div className="text-sm"><span className="text-zinc-500">Следующий шаг:</span> <input value={nextStep} onChange={e=>setNextStep(e.target.value)} placeholder="напр. Запустить дизайн-ревью" className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 ml-2 text-sm w-[260px]" /></div>
            <div className="text-xs text-zinc-500">Статус меняется через PATCH /api/v1/projects/{proj.slug}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-base">Быстрый запуск</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <Button className="w-full" onClick={()=>alert("Отправит bridge команду project.open → проверяет allowed_directories")}>▶ Открыть проект на PC</Button>
            <div className="text-xs text-zinc-500">Bridge проверит путь по allow-list. Телефон не имеет доступа к C:\\, только Bridge.</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle className="text-sm">Задачи ({tasks?.data?.length || 0})</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {tasks?.data?.length ? tasks.data.map((t:any)=>(
              <div key={t.id} className="flex justify-between items-center border border-zinc-800 rounded-xl px-3 py-2 text-sm">
                <span className="truncate">{t.title}</span><Badge variant="outline" className="text-[10px]">{t.status}</Badge>
              </div>
            )) : <div className="text-sm text-zinc-500">Нет связанных задач. Создай в Planner с выбором проекта.</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Заметки ({notes?.data?.length || 0})</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {notes?.data?.length ? notes.data.map((n:any)=>(
              <Link key={n.id} to={`/memory/${n.id}`} className="block border border-zinc-800 rounded-xl px-3 py-2 text-sm hover:bg-zinc-800">{n.title}</Link>
            )) : <div className="text-sm text-zinc-500">Нет связанных заметок. Свяжи из Memory по project_ids.</div>}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">История изменений</CardTitle></CardHeader>
        <CardContent><div className="text-xs text-zinc-500">Логи из /api/v1/settings/activity?entity_id={proj.id} — показывается после правок.</div></CardContent>
      </Card>
    </div>
  )
}
