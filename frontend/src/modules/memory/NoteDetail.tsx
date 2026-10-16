import { useParams, Link } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/api/client"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useState } from "react"

export default function NoteDetail(){
  const {id}=useParams()
  const qc=useQueryClient()
  const {data, isLoading, error}=useQuery({queryKey:["note",id], queryFn:()=>api.get<any>(`/notes/${id}`)})
  const [edit,setEdit]=useState(false)
  const [form,setForm]=useState({title:"",body:""})
  const update=useMutation({mutationFn:(p:any)=>api.patch(`/notes/${id}`,p), onSuccess:()=>{setEdit(false); qc.invalidateQueries({queryKey:["note",id]}); qc.invalidateQueries({queryKey:["notes"]})}})
  const del=useMutation({mutationFn:()=>api.del(`/notes/${id}`), onSuccess:()=>window.location.href="/memory"})
  if(isLoading) return <div className="text-zinc-500">Загрузка...</div>
  if(error) return <div className="text-red-400">{(error as Error).message}</div>
  if(!data) return null
  return (
    <div className="space-y-4 pb-20 max-w-3xl">
      <Link to="/memory" className="text-sm text-zinc-500">← Memory</Link>
      {!edit ? (
        <>
          <h1 className="text-2xl font-semibold">{data.title}</h1>
          <div className="text-xs text-zinc-500">{data.type} • {new Date(data.updated_at).toLocaleString("ru-RU")}</div>
          <Card><CardContent className="p-6 prose prose-invert max-w-none whitespace-pre-wrap text-sm leading-relaxed">{data.body || "— пусто —"}</CardContent></Card>
          <div className="flex gap-2">
            <Button variant="outline" onClick={()=>{setForm({title:data.title,body:data.body}); setEdit(true)}}>Редактировать</Button>
            <Button variant="ghost" onClick={()=>{if(confirm("Архивировать?")) del.mutate()}}>Архивировать</Button>
          </div>
        </>
      ) : (
        <Card className="border-[#4ADE80]/30">
          <CardHeader><CardTitle>Редактирование</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input value={form.title} onChange={e=>setForm({...form,title:e.target.value})} />
            <textarea value={form.body} onChange={e=>setForm({...form,body:e.target.value})} rows={10} className="w-full bg-zinc-900 border border-zinc-700 rounded-xl p-3 text-sm" />
            <div className="flex gap-2"><Button onClick={()=>update.mutate(form)}>Сохранить</Button><Button variant="outline" onClick={()=>setEdit(false)}>Отмена</Button></div>
          </CardContent>
        </Card>
      )}
      <Card><CardHeader><CardTitle className="text-sm">Связи и история</CardTitle></CardHeader><CardContent className="text-xs text-zinc-500">Связь с проектами — через project_ids при создании. История — GET /api/v1/notes/{id}/history</CardContent></Card>
    </div>
  )
}
