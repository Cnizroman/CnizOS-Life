import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "@/api/client"
import { useAuth } from "@/stores/auth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"

export default function Setup() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [name, setName] = useState("Owner")
  const [err, setErr] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const nav = useNavigate()
  const { setAuth } = useAuth()

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErr(null); setLoading(true)
    try {
      const res = await api.post<{ user: any; access_token: string }>("/auth/setup", { email, password, display_name: name })
      setAuth(res.user, res.access_token)
      nav("/")
    } catch (e: any) {
      setErr(e.message)
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0A0A0B] p-4">
      <Card className="w-full max-w-md border-zinc-800 bg-zinc-900">
        <CardHeader>
          <div className="w-10 h-10 rounded-xl bg-[#4ADE80] flex items-center justify-center font-bold text-black mb-2">C</div>
          <CardTitle className="text-xl">Первичная настройка CnizOS</CardTitle>
          <CardDescription>Создай единственного владельца. Повторная регистрация будет закрыта.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div><label className="text-sm text-zinc-400">Имя</label><Input value={name} onChange={e=>setName(e.target.value)} placeholder="Owner" /></div>
            <div><label className="text-sm text-zinc-400">Email</label><Input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com" required /></div>
            <div><label className="text-sm text-zinc-400">Пароль (мин 8)</label><Input type="password" value={password} onChange={e=>setPassword(e.target.value)} required minLength={8} /></div>
            {err && <div className="text-sm text-red-400 bg-red-950/50 border border-red-900 rounded-xl p-3">{err}</div>}
            <Button type="submit" disabled={loading} className="w-full">{loading ? "Создаётся..." : "Создать владельца →"}</Button>
            <p className="text-xs text-zinc-500 text-center">Backend: <code className="bg-zinc-800 px-1 rounded">POST /api/v1/auth/setup</code></p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
