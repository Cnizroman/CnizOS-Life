import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/api/client"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useState } from "react"

export default function PcControl(){
  const qc=useQueryClient()
  const {data:status}=useQuery({queryKey:["bridge-status"], queryFn:()=>api.get<any>("/bridge/status"), refetchInterval:5000})
  const {data:devices}=useQuery({queryKey:["bridge-devices"], queryFn:()=>api.get<any>("/bridge/devices")})
  const {data:actions}=useQuery({queryKey:["bridge-actions"], queryFn:()=>api.get<any>("/bridge/actions")})
  const {data:history}=useQuery({queryKey:["bridge-history"], queryFn:()=>api.get<any>("/bridge/commands?limit=20")})
  const [showReg,setShowReg]=useState(false)
  const [reg,setReg]=useState({name:"Main PC", allowed_apps:'[{"id":"vscode","label":"VS Code","exec":"C:\\\\Program Files\\\\Microsoft VS Code\\\\Code.exe"}]', allowed_dirs: '["C:\\\\Projects","D:\\\\Creative"]'})
  const [cmd,setCmd]=useState({bridge_id:"",action:"app.launch",params:'{"app_id":"vscode"}'})
  const register=useMutation({
    mutationFn:()=>api.post<any>("/bridge/devices",{name:reg.name, allowed_apps: JSON.parse(reg.allowed_apps), allowed_directories: JSON.parse(reg.allowed_dirs)}),
    onSuccess:(res)=>{alert(`Токен Bridge (сохрани!): ${res.bridge_token}`); qc.invalidateQueries({queryKey:["bridge-devices"]})}
  })
  const send=useMutation({
    mutationFn:()=>api.post<any>("/bridge/commands",{bridge_id: cmd.bridge_id, action: cmd.action, params: JSON.parse(cmd.params || "{}")}),
    onSuccess:()=>qc.invalidateQueries({queryKey:["bridge-history"]})
  })

  const online = status?.connected
  const devList = devices?.data || []
  if(devList.length && !cmd.bridge_id) setTimeout(()=>setCmd({...cmd, bridge_id: devList[0].id}),0)

  return (
    <div className="space-y-4 pb-20">
      <div className="flex justify-between items-center"><h1 className="text-2xl font-semibold">PC Control</h1><Badge variant={online?"default":"secondary"}>{online?"Bridge online":"Bridge offline"}</Badge></div>
      <Card className={online?"border-emerald-900 bg-emerald-950/20":"border-amber-900 bg-amber-950/20"}>
        <CardContent className="p-4 flex flex-wrap gap-3 items-center justify-between">
          <div><div className="font-medium">{online ? "Управление доступно" : "Компьютер не подключён"}</div><div className="text-sm text-zinc-400">{online ? "Команды отправятся через WSS Bridge" : "Запусти CnizOS-Bridge.exe на Windows. Пока — мок-исполнение."}</div></div>
          <Button variant="outline" onClick={()=>setShowReg(!showReg)}>+ Зарегистрировать Bridge</Button>
        </CardContent>
      </Card>
      {showReg && (
        <Card><CardHeader><CardTitle className="text-base">Новый Bridge</CardTitle></CardHeader><CardContent className="space-y-3">
          <Input value={reg.name} onChange={e=>setReg({...reg,name:e.target.value})} placeholder="Имя" />
          <div><label className="text-xs text-zinc-500">allowed_apps JSON</label><Input value={reg.allowed_apps} onChange={e=>setReg({...reg,allowed_apps:e.target.value})} /></div>
          <div><label className="text-xs text-zinc-500">allowed_directories JSON</label><Input value={reg.allowed_dirs} onChange={e=>setReg({...reg,allowed_dirs:e.target.value})} /></div>
          <Button onClick={()=>register.mutate()} disabled={register.isPending}>Зарегистрировать</Button>
          {register.isError && <div className="text-sm text-red-400">{(register.error as Error).message}</div>}
        </CardContent></Card>
      )}
      <div className="grid md:grid-cols-2 gap-4">
        <Card><CardHeader><CardTitle className="text-base">Устройства ({devList.length})</CardTitle></CardHeader><CardContent className="space-y-2">
          {devList.length ? devList.map((d:any)=>(
            <div key={d.id} className="border border-zinc-800 rounded-xl p-3">
              <div className="font-medium flex gap-2">{d.name}<Badge variant={d.status==="online"?"default":"secondary"} className="text-[10px]">{d.status}</Badge></div>
              <div className="text-xs text-zinc-500 mt-1">ID: {d.id.slice(0,8)} • last heartbeat: {d.last_heartbeat_at ? new Date(d.last_heartbeat_at).toLocaleString("ru-RU") : "never"}</div>
              <div className="text-xs text-zinc-400 mt-1">Apps: {d.allowed_apps?.map((a:any)=>a.id).join(", ")}</div>
              <div className="text-xs text-zinc-400">Dirs: {d.allowed_directories?.join(", ")}</div>
            </div>
          )) : <div className="text-sm text-zinc-500">Нет устройств. Зарегистрируй Bridge.</div>}
        </CardContent></Card>
        <Card><CardHeader><CardTitle className="text-base">Отправить команду</CardTitle></CardHeader><CardContent className="space-y-3">
          <select value={cmd.bridge_id} onChange={e=>setCmd({...cmd,bridge_id:e.target.value})} className="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm">
            {devList.map((d:any)=><option key={d.id} value={d.id}>{d.name}</option>)}
            {!devList.length && <option value="">— нет Bridge —</option>}
          </select>
          <select value={cmd.action} onChange={e=>setCmd({...cmd,action:e.target.value})} className="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-3 h-9 text-sm">
            {actions?.map((a:any)=><option key={a.id} value={a.id}>{a.id} — {a.description}</option>)}
          </select>
          <div><label className="text-xs text-zinc-500">params JSON</label><Input value={cmd.params} onChange={e=>setCmd({...cmd,params:e.target.value})} placeholder='{"app_id":"vscode"}' /></div>
          <Button onClick={()=>send.mutate()} disabled={!cmd.bridge_id || send.isPending} className="w-full">▶ Выполнить</Button>
          {send.data && <div className="text-xs p-2 rounded bg-zinc-900 border border-zinc-800"><div>status: {send.data.status}</div><div>id: {send.data.command_id}</div>{send.data.error && <div className="text-red-400">{send.data.error}</div>}</div>}
          {send.isError && <div className="text-sm text-red-400">{(send.error as Error).message}</div>}
          <div className="text-xs text-zinc-500">Безопасность: проверяется на сервере и повторно на Bridge. Запрещённые пути/приложения — отклонятся с error_code.</div>
        </CardContent></Card>
      </div>
      <Card><CardHeader><CardTitle className="text-base">История команд</CardTitle></CardHeader><CardContent className="space-y-2">
        {history?.data?.length ? history.data.map((c:any)=>(
          <div key={c.id} className="border border-zinc-800 rounded-xl p-3 flex justify-between items-center">
            <div><div className="font-mono text-xs">{c.action} <span className="text-zinc-500">{JSON.stringify(c.params)}</span></div><div className="text-xs text-zinc-500">{new Date(c.requested_at).toLocaleString("ru-RU")}</div></div>
            <Badge variant={c.status==="succeeded"?"default": c.status==="failed"?"destructive":"secondary"}>{c.status}</Badge>
          </div>
        )) : <div className="text-sm text-zinc-500">Нет команд.</div>}
      </CardContent></Card>
    </div>
  )
}
