import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/api/client"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useState } from "react"

export default function Automation(){
  const qc=useQueryClient()
  const {data}=useQuery({queryKey:["scenarios"], queryFn:()=>api.get<any>("/automation/scenarios")})
  const {data:runs}=useQuery({queryKey:["runs"], queryFn:()=>api.get<any>("/automation/runs")})
  const [show,setShow]=useState(false)
  const [form,setForm]=useState({name:"",steps:'[{"action":"app.launch","params":{"app_id":"vscode"},"position":0},{"action":"system.volume.set","params":{"level":30},"position":1}]'})
  const create=useMutation({
    mutationFn:()=>api.post<any>("/automation/scenarios",{name:form.name, steps: JSON.parse(form.steps)}),
    onSuccess:()=>{setShow(false); setForm({name:"",steps:'[]'}); qc.invalidateQueries({queryKey:["scenarios"]})}
  })
  const run=useMutation({
    mutationFn:(id:string)=>api.post<any>(`/automation/scenarios/${id}/run`,{}),
    onSuccess:()=>qc.invalidateQueries({queryKey:["runs"]})
  })
  return (
    <div className="space-y-4 pb-20">
      <div className="flex justify-between items-center"><h1 className="text-2xl font-semibold">Automation</h1><Button onClick={()=>setShow(!show)}>+ Сценарий</Button></div>
      {show && (
        <Card className="border-[#4ADE80]/30"><CardHeader><CardTitle className="text-base">Новый сценарий</CardTitle></CardHeader><CardContent className="space-y-3">
          <Input placeholder="Название, напр. Режим разработки" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} />
          <div><label className="text-xs text-zinc-500">steps JSON — фиксированный набор действий</label><textarea value={form.steps} onChange={e=>setForm({...form,steps:e.target.value})} rows={4} className="w-full bg-zinc-900 border border-zinc-700 rounded-xl p-3 text-xs font-mono" /></div>
          <div className="text-xs text-zinc-500">Доступные: app.launch, folder.open, project.open, system.volume.set, system.status.get, profile.activate</div>
          <div className="flex gap-2"><Button onClick={()=>create.mutate()} disabled={!form.name.trim()}>Создать</Button><Button variant="outline" onClick={()=>setShow(false)}>Отмена</Button></div>
        </CardContent></Card>
      )}
      <div className="grid md:grid-cols-2 gap-4">
        <Card><CardHeader><CardTitle className="text-base">Сценарии</CardTitle></CardHeader><CardContent className="space-y-2">
          {data?.data?.length ? data.data.map((s:any)=>(
            <div key={s.id} className="border border-zinc-800 rounded-xl p-3">
              <div className="font-medium flex gap-2">{s.name} <Badge variant={s.is_enabled?"default":"secondary"} className="text-[10px]">{s.is_enabled?"enabled":"disabled"}</Badge></div>
              <div className="text-xs text-zinc-500">{s.steps?.length || 0} шагов • {s.trigger_type}</div>
              <div className="mt-2 space-y-1">
                {s.steps?.map((st:any,i:number)=><div key={i} className="text-xs font-mono bg-zinc-900 rounded px-2 py-1 text-zinc-400">{st.position}: {st.action} {JSON.stringify(st.params)}</div>)}
              </div>
              <Button size="sm" className="mt-2 w-full" onClick={()=>run.mutate(s.id)} disabled={run.isPending}>▶ Запустить</Button>
            </div>
          )) : <div className="text-sm text-zinc-500">Нет сценариев. Создай «Режим разработки» → VS Code + проект + громкость.</div>}
        </CardContent></Card>
        <Card><CardHeader><CardTitle className="text-base">История запусков</CardTitle></CardHeader><CardContent className="space-y-2">
          {runs?.data?.length ? runs.data.map((r:any)=>(
            <div key={r.id} className="border border-zinc-800 rounded-xl p-3">
              <div className="flex justify-between"><span className="text-xs font-mono">{r.scenario_id.slice(0,8)}</span><Badge variant={r.status==="succeeded"?"default": r.status==="failed"?"destructive":"secondary"}>{r.status}</Badge></div>
              <div className="text-xs text-zinc-500 mt-1">{new Date(r.started_at).toLocaleString("ru-RU")} → {r.finished_at ? new Date(r.finished_at).toLocaleString("ru-RU") : "—"}</div>
              <div className="text-xs mt-1 space-y-1">{r.step_results?.map((st:any,i:number)=><div key={i} className={`px-2 py-0.5 rounded ${st.status==="succeeded"?"bg-emerald-950/50 text-emerald-400":"bg-red-950/50 text-red-400"}`}>{st.action}: {st.status}</div>)}</div>
            </div>
          )) : <div className="text-sm text-zinc-500">Нет запусков.</div>}
        </CardContent></Card>
      </div>
      <Card className="border-dashed"><CardContent className="p-4 text-xs text-zinc-500">Сценарии выполняются последовательно. Критическая ошибка — стоп или переход по continue_on_error. Журнал — /api/v1/automation/runs</CardContent></Card>
    </div>
  )
}
