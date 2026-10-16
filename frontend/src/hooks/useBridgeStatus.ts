import { useQuery } from "@tanstack/react-query"
import { api } from "@/api/client"

type BridgeStatus = {
  connected: boolean
  devices: { id: string; name: string; status: string; last_heartbeat_at: string | null }[]
}

export function useBridgeStatus() {
  return useQuery({
    queryKey: ["bridge-status"],
    queryFn: () => api.get<BridgeStatus>("/bridge/status"),
    refetchInterval: 15000,
    retry: false,
  })
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => fetch("/api/health").then(r => r.json()).catch(() => api.get("/health").catch(() => ({ status: "offline" }))),
    refetchInterval: 15000,
    retry: false,
  })
}
