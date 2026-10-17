import { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { api } from "@/api/client"
import { useAuth } from "@/stores/auth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"

export default function Login() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [err, setErr] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const nav = useNavigate()
  const { setAuth } = useAuth()

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErr(null); setLoading(true)
    try {
      const res = await api.post<{ user: any; access_token: string }>("/auth/login", { email, password })
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
          <CardTitle>Вход в CnizOS</CardTitle>
          <CardDescription>Введи данные владельца</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div><label className="text-sm text-zinc-400">Email</label><Input type="email" value={email} onChange={e=>setEmail(e.target.value)} required /></div>
            <div><label className="text-sm text-zinc-400">Пароль</label><Input type="password" value={password} onChange={e=>setPassword(e.target.value)} required /></div>
            {err && <div className="text-sm text-red-400 bg-red-950/50 border border-red-900 rounded-xl p-3">{err}</div>}
            <Button type="submit" disabled={loading} className="w-full">{loading ? "Вход..." : "Войти"}</Button>
            <p className="text-xs text-center text-zinc-500">Нет аккаунта? <Link to="/setup" className="text-[#4ADE80] hover:underline">Первичная настройка</Link></p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
