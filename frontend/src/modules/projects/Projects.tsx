import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/api/client"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Link } from "react-router-dom"
import { useState } from "react"

export default function Projects(){
  const [q,setQ]=useState("")
  const [status,setStatus]=useState("")
  const [showCreate,setShowCreate]=useState(false)
  const [form,setForm]=useState({title:"",description:"",category:"other",status:"idea",priority:"medium",github_url:"",deadline:""})
  const qc=useQueryClient()
  const {data, isLoading, error} = useQuery({queryKey:["projects",q,status], queryFn:()=>api.get<any>(`/projects?q=${encodeURIComponent(q)}&status=${status}`), retry:false})
  const create=useMutation({
    mutationFn:()=>api.post<any>("/projects",{title:form.title,description:form.description,category:form.category,status:form.status,priority:form.priority,github_url:form.github_url||undefined,deadline:form.deadline||undefined}),
    onSuccess:()=>{setShowCreate(false); setForm({title:"",description:"",category:"other",status:"idea",priority:"medium",github_url:"",deadline:""}); qc.invalidateQueries({queryKey:["projects"]})}
  })
  if(isLoading) return <div className="text-zinc-500">Загрузка проектов...</div>
  if(error) return <div className="rounded-xl bg-amber-950/30 border border-amber-900 p-4 text-amber-200">Ошибка: {(error as Error).message}</div>
  const list = data?.data || []
  return (
    <div className="space-y-4 pb-20">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <h1 className="text-2xl font-semibold">Projects <span className="text-sm font-normal text-zinc-500">{data?.meta?.total ?? list.length}</span></h1>
        <Button onClick={()=>setShowCreate(!showCreate)}>+ Новый проект</Button>
      </div>
      <div className="flex flex-wrap gap-2">
        <Input placeholder="Поиск..." value={q} onChange={e=>setQ(e.target.value)} className="max-w-[260px]" />
        <select value={status} onChange={e=>setStatus(e.target.value)} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 text-sm h-9">
          <option value="">Все статусы</option><option value="idea">idea</option><option value="active">active</option><option value="paused">paused</option><option value="done">done</option><option value="archived">archived</option>
        </select>
      </div>
      {showCreate && (
        <Card className="border-[#4ADE80]/30">
          <CardHeader><CardTitle className="text-base">Создать проект</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="Название *" value={form.title} onChange={e=>setForm({...form,title:e.target.value})} />
            <Input placeholder="Описание" value={form.description} onChange={e=>setForm({...form,description:e.target.value})} />
            <div className="grid grid-cols-2 gap-3">
              <select value={form.category} onChange={e=>setForm({...form,category:e.target.value})} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm"><option value="site">site</option><option value="app">app</option><option value="creative">creative</option><option value="tool">tool</option><option value="study">study</option><option value="other">other</option></select>
              <select value={form.status} onChange={e=>setForm({...form,status:e.target.value})} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm"><option value="idea">idea</option><option value="active">active</option><option value="paused">paused</option><option value="done">done</option></select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <select value={form.priority} onChange={e=>setForm({...form,priority:e.target.value})} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm"><option value="low">low</option><option value="medium">medium</option><option value="high">high</option><option value="critical">critical</option></select>
              <Input placeholder="GitHub URL" value={form.github_url} onChange={e=>setForm({...form,github_url:e.target.value})} />
            </div>
            <Input type="date" value={form.deadline} onChange={e=>setForm({...form,deadline:e.target.value})} />
            <div className="flex gap-2">
              <Button onClick={()=>create.mutate()} disabled={!form.title.trim() || create.isPending}>{create.isPending?"Создание...":"Создать"}</Button>
              <Button variant="outline" onClick={()=>setShowCreate(false)}>Отмена</Button>
            </div>
            {create.isError && <div className="text-sm text-red-400">{(create.error as Error).message}</div>}
          </CardContent>
        </Card>
      )}
      {list.length===0 ? (
        <Card><CardContent className="p-8 text-center text-zinc-500">Нет проектов. Создай первый — он сохранится в PostgreSQL.<br/><span className="text-xs">POST /api/v1/projects</span></CardContent></Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {list.map((p:any)=>(
            <Link key={p.id} to={`/projects/${p.slug}`} className="block">
              <Card className="hover:border-zinc-700 transition-colors h-full">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2"><Badge variant="secondary" className="text-[10px]">{p.category}</Badge><Badge variant={p.status==="active"?"default":"outline"} className="text-[10px]">{p.status}</Badge><Badge variant="outline" className="ml-auto text-[10px]">{p.priority}</Badge></div>
                  <CardTitle className="text-base mt-2 leading-tight">{p.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-zinc-400 line-clamp-2 min-h-[40px]">{p.description || "Нет описания"}</div>
                  <div className="flex gap-2 mt-3 text-xs text-zinc-500">
                    {p.github_url && <span className="truncate">GitHub</span>}
                    {p.deadline && <span>до {new Date(p.deadline).toLocaleDateString("ru-RU")}</span>}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
