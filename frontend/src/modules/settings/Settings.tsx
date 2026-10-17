import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/api/client"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useTheme } from "@/stores/theme"
import { useAuth } from "@/stores/auth"
import { useState } from "react"

export default function Settings(){
  const {theme,setTheme,accent,setAccent}=useTheme()
  const {user,logout}=useAuth()
  const qc=useQueryClient()
  const {data:settings}=useQuery({queryKey:["settings"], queryFn:()=>api.get<any>("/settings")})
  const {data:activity}=useQuery({queryKey:["activity"], queryFn:()=>api.get<any>("/settings/activity?limit=20")})
  const {data:devices}=useQuery({queryKey:["devices"], queryFn:()=>api.get<any>("/devices")})
  const {data:sessions}=useQuery({queryKey:["sessions"], queryFn:()=>api.get<any>("/auth/sessions")})
  const [newPass,setNewPass]=useState("")
  const save=useMutation({mutationFn:(p:any)=>api.patch("/settings",p), onSuccess:()=>qc.invalidateQueries({queryKey:["settings"]})})
  const backup=useMutation({mutationFn:()=>api.post<any>("/settings/backup")})

  return (
    <div className="space-y-6 pb-20">
      <h1 className="text-2xl font-semibold">Settings</h1>

      <div className="grid md:grid-cols-2 gap-4">
        <Card><CardHeader><CardTitle className="text-base">Интерфейс</CardTitle></CardHeader><CardContent className="space-y-3">
          <div className="flex gap-2">
            <Button variant={theme==="dark"?"default":"outline"} onClick={()=>{setTheme("dark"); save.mutate({theme:"dark"})}}>Тёмная</Button>
            <Button variant={theme==="light"?"default":"outline"} onClick={()=>{setTheme("light"); save.mutate({theme:"light"})}}>Светлая</Button>
          </div>
          <div className="flex items-center gap-2"><span className="text-sm text-zinc-400">Акцент</span><input type="color" value={accent} onChange={e=>{setAccent(e.target.value); save.mutate({accent:e.target.value})}} className="w-8 h-8 rounded" /> <span className="text-xs text-zinc-500">{accent}</span></div>
          <div className="text-xs text-zinc-500">Текущая тема: {settings?.theme} • Плотность: {settings?.density}</div>
        </CardContent></Card>

        <Card><CardHeader><CardTitle className="text-base">Устройства и сессии</CardTitle></CardHeader><CardContent className="space-y-2">
          <div className="text-sm font-medium">Подключённые устройства: {devices?.data?.length || 0}</div>
          {devices?.data?.map((d:any)=><div key={d.id} className="text-xs border border-zinc-800 rounded p-2 flex justify-between"><span>{d.name} ({d.platform})</span><span className="text-zinc-500">{new Date(d.last_seen_at).toLocaleDateString("ru-RU")}</span></div>)}
          <div className="text-sm font-medium mt-3">Сессии: {sessions?.data?.length || 0}</div>
          {sessions?.data?.slice(0,3).map((s:any)=><div key={s.id} className="text-xs border border-zinc-800 rounded p-2 truncate">{s.user_agent?.slice(0,60) || "—"} • {new Date(s.created_at).toLocaleString("ru-RU")}</div>)}
          <Button variant="outline" size="sm" onClick={async()=>{await api.post("/auth/logout"); logout(); window.location.href="/login"}}>Выйти везде</Button>
        </CardContent></Card>
      </div>

      <Card><CardHeader><CardTitle className="text-base">Безопасность</CardTitle></CardHeader><CardContent className="space-y-3">
        <div className="text-sm">Пользователь: <span className="font-medium">{user?.email}</span> • {user?.display_name}</div>
        <div className="flex gap-2"><Input placeholder="Новый пароль (мин 8)" value={newPass} onChange={e=>setNewPass(e.target.value)} className="max-w-[260px]" /><Button variant="outline" onClick={()=>alert("Смена пароля — PATCH /api/v1/auth/me (добавь в backend при необходимости)")}>Сменить</Button></div>
        <div className="text-xs text-zinc-500">Секреты и токены Bridge/Zoro не показываются целиком после сохранения.</div>
      </CardContent></Card>

      <Card><CardHeader><CardTitle className="text-base">Интеграции</CardTitle></CardHeader><CardContent className="space-y-2 text-sm">
        <div className="flex justify-between"><span>Zoro</span><Badge variant={settings?.zoro_enabled?"default":"secondary"}>{settings?.zoro_enabled?"enabled":"disabled"}</Badge></div>
        <div className="text-xs text-zinc-500">Токен Zoro хранится как hash в integration_settings. Управление — через /api/v1/settings.</div>
        <div className="flex justify-between"><span>Bridge auto-connect</span><Badge>{settings?.bridge_auto_connect?"on":"off"}</Badge></div>
      </CardContent></Card>

      <Card><CardHeader><CardTitle className="text-base">Резервное копирование</CardTitle></CardHeader><CardContent className="space-y-3">
        <Button onClick={()=>backup.mutate()}>Создать бэкап</Button>
        {backup.data && <div className="text-xs p-2 bg-zinc-900 rounded border border-zinc-800">Путь: {backup.data.path} • {backup.data.size} bytes<br/>Для postgres: pg_dump в prod.</div>}
        <div className="text-xs text-zinc-500">Восстановление: загрузи файл на /api/v1/settings/restore. Храни бэкапы вне сервера.</div>
      </CardContent></Card>

      <Card><CardHeader><CardTitle className="text-base">Журнал действий</CardTitle></CardHeader><CardContent className="space-y-1">
        {activity?.data?.slice(0,10).map((a:any)=><div key={a.id} className="text-xs border border-zinc-800 rounded p-2 flex justify-between"><span>{a.action} <span className="text-zinc-500">{a.entity_type || ""}</span></span><span className="text-zinc-500">{new Date(a.created_at).toLocaleString("ru-RU")}</span></div>)}
        {!activity?.data?.length && <div className="text-sm text-zinc-500">Нет записей.</div>}
      </CardContent></Card>
    </div>
  )
}
