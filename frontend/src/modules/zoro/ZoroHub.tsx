import { useQuery, useMutation } from "@tanstack/react-query"
import { api } from "@/api/client"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useState } from "react"

export default function ZoroHub(){
  const {data:status}=useQuery({queryKey:["zoro-bridge"], queryFn:()=>api.get<any>("/zoro/bridge/status"), retry:false})
  const {data:history}=useQuery({queryKey:["zoro-history"], queryFn:()=>api.get<any>("/zoro/history"), retry:false})
  const {data:tasks}=useQuery({queryKey:["zoro-tasks"], queryFn:()=>api.get<any>("/zoro/tasks?view=today"), retry:false})
  const [test,setTest]=useState('{"action":"app.launch","params":{"app_id":"vscode"}}')
  const run=useMutation({mutationFn:()=>api.post<any>("/zoro/actions/execute", JSON.parse(test))})
  const [note,setNote]=useState("проверить новый дизайн")
  const saveNote=useMutation({mutationFn:()=>api.post<any>("/zoro/notes",{title: note, body: note})})
  return (
    <div className="space-y-4 pb-20">
      <h1 className="text-2xl font-semibold">Zoro Hub</h1>
      <div className="grid md:grid-cols-3 gap-4">
        <Card><CardHeader><CardTitle className="text-sm">Состояние</CardTitle></CardHeader><CardContent className="space-y-2 text-sm">
          <div className="flex justify-between"><span>Zoro подключён</span><Badge variant="default">через API</Badge></div>
          <div className="flex justify-between"><span>Bridge</span><Badge variant={status?.devices?.length?"default":"secondary"}>{status?.devices?.length ? "online" : "offline"}</Badge></div>
          <div className="text-xs text-zinc-500">Zoro сохраняет команду → cnizos_client.py → /api/v1/zoro/* → Bridge → результат</div>
        </CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Быстрые голосовые сценарии</CardTitle></CardHeader><CardContent className="text-xs space-y-1 text-zinc-400">
          <div>“Зоро, сохрани заметку: проверить новый дизайн” → POST /zoro/notes</div>
          <div>“Зоро, добавь задачу на завтра — исправить сайт” → POST /zoro/tasks</div>
          <div>“Зоро, какие задачи на сегодня?” → GET /zoro/tasks?view=today ({tasks?.data?.length || 0})</div>
          <div>“Зоро, открой проект Зоро” → POST /zoro/actions/execute</div>
        </CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Последний ответ Bridge</CardTitle></CardHeader><CardContent className="text-xs text-zinc-400">
          {run.data ? <div className="p-2 bg-zinc-900 rounded border border-zinc-800"><div>status: {run.data.status}</div><div>result: {JSON.stringify(run.data.result)}</div></div> : <div>Нет данных — протестируй команду.</div>}
        </CardContent></Card>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Card><CardHeader><CardTitle className="text-base">Тест команды</CardTitle></CardHeader><CardContent className="space-y-3">
          <div><label className="text-xs text-zinc-500">JSON для /zoro/actions/execute</label><Input value={test} onChange={e=>setTest(e.target.value)} className="font-mono text-xs" /></div>
          <Button onClick={()=>run.mutate()} className="w-full">▶ Отправить как Зоро</Button>
          {run.isError && <div className="text-sm text-red-400">{(run.error as Error).message}</div>}
        </CardContent></Card>
        <Card><CardHeader><CardTitle className="text-base">Создать заметку голосом</CardTitle></CardHeader><CardContent className="space-y-3">
          <Input value={note} onChange={e=>setNote(e.target.value)} placeholder="текст заметки" />
          <Button onClick={()=>saveNote.mutate()} className="w-full">💾 Сохранить через Zoro API</Button>
          {saveNote.data && <div className="text-xs text-emerald-400">Сохранено: {saveNote.data.id}</div>}
        </CardContent></Card>
      </div>

      <Card><CardHeader><CardTitle className="text-base">Журнал Zoro</CardTitle></CardHeader><CardContent className="space-y-2">
        {history?.data?.length ? history.data.map((h:any,i:number)=>(
          <div key={i} className="border border-zinc-800 rounded-xl p-2 flex justify-between text-xs">
            <span>{h.action}</span><span className="text-zinc-500">{new Date(h.created_at).toLocaleString("ru-RU")}</span>
          </div>
        )) : <div className="text-sm text-zinc-500">Пока нет записей. Команды появятся после вызовов cnizos_client.py</div>}
        <div className="text-xs text-zinc-500 mt-2">Разделы: помощник запущен / подключён / команда выполняется / завершена / ошибка — из реального состояния.</div>
      </CardContent></Card>

      <Card className="border-dashed"><CardContent className="p-4 text-xs text-zinc-500">Интеграция: скопируй <code>integrations/zoro/cnizos_client.py</code> в папку Зоро, укажи <code>cnizos_url</code> и <code>zoro_token</code> из Settings. См. docs/zoro-integration.md</CardContent></Card>
    </div>
  )
}
