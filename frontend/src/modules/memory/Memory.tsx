import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/api/client"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Link } from "react-router-dom"
import { useState } from "react"

export default function Memory(){
  const [q,setQ]=useState("")
  const [type,setType]=useState("")
  const [show,setShow]=useState(false)
  const [form,setForm]=useState({title:"",body:"",type:"note",collection:""})
  const qc=useQueryClient()
  const {data, isLoading, error}=useQuery({queryKey:["notes",q,type], queryFn:()=>api.get<any>(`/notes?q=${encodeURIComponent(q)}&type=${type}`)})
  const create=useMutation({
    mutationFn:()=>api.post<any>("/notes",{title:form.title,body:form.body,type:form.type,collection:form.collection||undefined}),
    onSuccess:()=>{setShow(false); setForm({title:"",body:"",type:"note",collection:""}); qc.invalidateQueries({queryKey:["notes"]})}
  })
  if(isLoading) return <div className="text-zinc-500">Загрузка...</div>
  if(error) return <div className="text-amber-200">{(error as Error).message}</div>
  const list = data?.data || []
  return (
    <div className="space-y-4 pb-20">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <h1 className="text-2xl font-semibold">Memory</h1>
        <Button onClick={()=>setShow(!show)}>+ Заметка</Button>
      </div>
      <div className="flex flex-wrap gap-2">
        <Input placeholder="Поиск по заголовку и Markdown..." value={q} onChange={e=>setQ(e.target.value)} className="max-w-[320px]" />
        <select value={type} onChange={e=>setType(e.target.value)} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm">
          <option value="">Все типы</option><option value="note">note</option><option value="idea">idea</option><option value="tech">tech</option><option value="bug">bug</option><option value="instruction">instruction</option><option value="link">link</option>
        </select>
      </div>
      {show && (
        <Card className="border-[#4ADE80]/30">
          <CardHeader><CardTitle className="text-base">Новая запись</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="Заголовок *" value={form.title} onChange={e=>setForm({...form,title:e.target.value})} />
            <textarea placeholder="Markdown..." value={form.body} onChange={e=>setForm({...form,body:e.target.value})} rows={4} className="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-3 py-2 text-sm" />
            <div className="grid grid-cols-2 gap-3">
              <select value={form.type} onChange={e=>setForm({...form,type:e.target.value})} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm">
                <option value="note">note</option><option value="idea">idea</option><option value="link">link</option><option value="tech">tech</option><option value="bug">bug</option><option value="instruction">instruction</option>
              </select>
              <Input placeholder="Коллекция (напр. Zoro)" value={form.collection} onChange={e=>setForm({...form,collection:e.target.value})} />
            </div>
            <div className="flex gap-2"><Button onClick={()=>create.mutate()} disabled={!form.title.trim()}>Сохранить</Button><Button variant="outline" onClick={()=>setShow(false)}>Отмена</Button></div>
          </CardContent>
        </Card>
      )}
      {list.length===0 ? <Card><CardContent className="p-8 text-center text-zinc-500">Нет заметок. Создай с Markdown, тегами и связью с проектом.<br/><span className="text-xs">POST /api/v1/notes — поиск через PostgreSQL FTS (здесь LIKE для SQLite)</span></CardContent></Card> :
        <div className="grid md:grid-cols-2 gap-3">
          {list.map((n:any)=>(
            <Link key={n.id} to={`/memory/${n.id}`}>
              <Card className="hover:border-zinc-700 h-full">
                <CardHeader className="pb-2">
                  <div className="flex gap-2"><Badge variant="secondary" className="text-[10px]">{n.type}</Badge>{n.is_pinned && <Badge className="text-[10px]"> pinned</Badge>}{n.collection && <Badge variant="outline" className="text-[10px]">{n.collection}</Badge>}</div>
                  <CardTitle className="text-base mt-1">{n.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-zinc-400 line-clamp-3 whitespace-pre-wrap">{n.body?.slice(0,180) || "—"}</div>
                  <div className="text-xs text-zinc-600 mt-2">{new Date(n.updated_at).toLocaleString("ru-RU")}</div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      }
    </div>
  )
}
