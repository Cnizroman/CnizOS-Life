import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/api/client"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useState } from "react"

export default function Creative(){
  const [show,setShow]=useState(false)
  const [form,setForm]=useState({title:"",type:"other",collection:"",external_url:""})
  const [filter,setFilter]=useState("")
  const qc=useQueryClient()
  const {data}=useQuery({queryKey:["creative",filter], queryFn:()=>api.get<any>(`/creative/assets?q=${encodeURIComponent(filter)}`)})
  const create=useMutation({mutationFn:()=>api.post<any>("/creative/assets",{title:form.title,type:form.type,collection:form.collection||undefined,external_url:form.external_url||undefined}), onSuccess:()=>{setShow(false); setForm({title:"",type:"other",collection:"",external_url:""}); qc.invalidateQueries({queryKey:["creative"]})}})
  const del=useMutation({mutationFn:(id:string)=>api.del(`/creative/assets/${id}`), onSuccess:()=>qc.invalidateQueries({queryKey:["creative"]})})
  const upload=useMutation({
    mutationFn: async ({id,file}:{id:string,file:File})=>{
      const fd=new FormData()
      fd.append("file",file)
      const token=localStorage.getItem("cnizos_access_token")
      const res=await fetch(`/api/v1/creative/assets/${id}/upload`,{method:"POST",headers:{Authorization:`Bearer ${token}`}, body:fd})
      if(!res.ok) throw new Error(await res.text())
      return res.json()
    },
    onSuccess:()=>qc.invalidateQueries({queryKey:["creative"]})
  })
  return (
    <div className="space-y-4 pb-20">
      <div className="flex justify-between items-center"><h1 className="text-2xl font-semibold">Creative</h1><Button onClick={()=>setShow(!show)}>+ Материал</Button></div>
      <Input placeholder="Поиск по творческим материалам..." value={filter} onChange={e=>setFilter(e.target.value)} className="max-w-[320px]" />
      {show && (
        <Card className="border-[#4ADE80]/30"><CardHeader><CardTitle className="text-base">Новый материал</CardTitle></CardHeader><CardContent className="space-y-3">
          <Input placeholder="Название *" value={form.title} onChange={e=>setForm({...form,title:e.target.value})} />
          <div className="grid grid-cols-2 gap-3">
            <select value={form.type} onChange={e=>setForm({...form,type:e.target.value})} className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm"><option value="music">music</option><option value="cover">cover</option><option value="photo">photo</option><option value="design">design</option><option value="video">video</option><option value="text">text</option><option value="other">other</option></select>
            <Input placeholder="Коллекция" value={form.collection} onChange={e=>setForm({...form,collection:e.target.value})} />
          </div>
          <Input placeholder="External URL (SoundCloud, Behance...)" value={form.external_url} onChange={e=>setForm({...form,external_url:e.target.value})} />
          <div className="flex gap-2"><Button onClick={()=>create.mutate()} disabled={!form.title.trim()}>Создать</Button><Button variant="outline" onClick={()=>setShow(false)}>Отмена</Button></div>
        </CardContent></Card>
      )}
      <div className="grid md:grid-cols-3 gap-3">
        {data?.data?.length ? data.data.map((a:any)=>(
          <Card key={a.id} className="hover:border-zinc-700">
            <CardHeader className="pb-2"><div className="flex gap-2"><span className="text-xs px-2 py-0.5 rounded-full bg-zinc-800">{a.type}</span>{a.collection && <span className="text-xs px-2 py-0.5 rounded-full bg-[#4ADE80]/20 text-[#4ADE80]">{a.collection}</span>}</div><CardTitle className="text-base mt-1">{a.title}</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <div className="text-xs text-zinc-500">{new Date(a.created_at).toLocaleDateString("ru-RU")}</div>
              {a.external_url && <a href={a.external_url} target="_blank" className="text-xs text-[#4ADE80] block truncate">{a.external_url}</a>}
              <label className="block">
                <span className="text-xs text-zinc-400">Загрузить файл (до 100MB)</span>
                <input type="file" onChange={e=>{const f=e.target.files?.[0]; if(f) upload.mutate({id:a.id,file:f})}} className="block w-full text-xs mt-1" />
              </label>
              {a.storage_key && <div className="text-xs text-emerald-400 truncate">✓ {a.storage_key}</div>}
              <Button variant="ghost" size="sm" onClick={()=>del.mutate(a.id)} className="w-full text-red-400">Удалить</Button>
            </CardContent>
          </Card>
        )) : <Card className="col-span-3"><CardContent className="p-8 text-center text-zinc-500">Нет материалов — создай коллекцию, добавь музыку/обложки/фото. Файлы хранятся в <code>storage/creative/&lt;id&gt;</code>, не в БД.</CardContent></Card>}
      </div>
    </div>
  )
}
