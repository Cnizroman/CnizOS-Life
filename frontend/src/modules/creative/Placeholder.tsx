import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
export default function Placeholder(){
  return (
    <div className="space-y-4 pb-20">
      <div className="flex items-center gap-3"><h1 className="text-2xl font-semibold">Creative</h1><Badge variant="secondary">Этап creative</Badge></div>
      <Card><CardHeader><CardTitle>Модуль в разработке</CardTitle></CardHeader><CardContent className="text-sm text-zinc-400">Дизайн и API уже спроектированы (см. docs/). Реальная логика — следующие этапы. Все статусы будут из реального backend, без фиктивных данных.</CardContent></Card>
    </div>
  )
}
