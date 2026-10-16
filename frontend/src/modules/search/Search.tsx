import { useSearchParams, Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/api/client"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { useState, useEffect } from "react"

export default function SearchPage(){
  const [params,setParams]=useSearchParams()
  const q = params.get("q") || ""
  const [input,setInput]=useState(q)
  useEffect(()=>setInput(q),[q])
  const {data, isLoading}=useQuery({queryKey:["search",q], queryFn:()=>api.get<any>(`/search?q=${encodeURIComponent(q)}`), enabled: !!q})
  const submit=(e:React.FormEvent)=>{e.preventDefault(); setParams({q:input})}
  return (
    <div className="space-y-4 pb-20 max-w-3xl">
      <h1 className="text-2xl font-semibold">Поиск</h1>
      <form onSubmit={submit} className="flex gap-2">
        <Input placeholder="Запрос..." value={input} onChange={e=>setInput(e.target.value)} />
        <button type="submit" className="bg-[#4ADE80] text-black px-4 rounded-xl text-sm font-medium">Найти</button>
      </form>
      {!q ? <div className="text-zinc-500 text-sm">Введи запрос — ищет по проектам, задачам и заметкам (PostgreSQL FTS).</div> :
        isLoading ? <div className="text-zinc-500">Поиск...</div> :
        <div className="space-y-2">
          <div className="text-sm text-zinc-500">{data?.results?.length || 0} результатов для "{q}"</div>
          {data?.results?.map((r:any)=>(
            <Link key={r.type+r.id} to={r.url} className="block">
              <Card className="hover:border-zinc-700">
                <CardContent className="p-4">
                  <div className="flex gap-2 items-center"><span className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400">{r.type}</span><span className="font-medium">{r.title}</span></div>
                  <div className="text-sm text-zinc-400 mt-1 line-clamp-2" dangerouslySetInnerHTML={{__html: r.snippet}} />
                  <div className="text-xs text-[#4ADE80] mt-1">{r.url}</div>
                </CardContent>
              </Card>
            </Link>
          ))}
          {data?.results?.length===0 && <Card><CardContent className="p-8 text-center text-zinc-500">Ничего не найдено — попробуй другой запрос.</CardContent></Card>}
        </div>
      }
    </div>
  )
}
