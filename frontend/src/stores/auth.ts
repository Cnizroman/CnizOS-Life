import { create } from "zustand"

type User = {
  id: string
  email: string
  display_name: string
}

type AuthState = {
  user: User | null
  token: string | null
  isSetupRequired: boolean | null
  setAuth: (user: User | null, token: string | null) => void
  setSetupRequired: (v: boolean) => void
  logout: () => void
}

export const useAuth = create<AuthState>((set) => ({
  user: JSON.parse(localStorage.getItem("cnizos_user") || "null"),
  token: localStorage.getItem("cnizos_access_token"),
  isSetupRequired: null,
  setAuth: (user, token) => {
    if (user) localStorage.setItem("cnizos_user", JSON.stringify(user))
    else localStorage.removeItem("cnizos_user")
    if (token) localStorage.setItem("cnizos_access_token", token)
    else localStorage.removeItem("cnizos_access_token")
    set({ user, token })
  },
  setSetupRequired: (v) => set({ isSetupRequired: v }),
  logout: () => {
    localStorage.removeItem("cnizos_user")
    localStorage.removeItem("cnizos_access_token")
    set({ user: null, token: null })
  },
}))
