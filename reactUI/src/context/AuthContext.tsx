import { createContext, useContext, useMemo, useState } from 'react'
import { jwtDecode } from 'jwt-decode'
import type { AuthClaims } from '../types'
import { api } from '../api/client'

interface AuthState extends AuthClaims { token: string }

interface AuthContextValue {
  user: AuthState | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthState | null>(null)

  const login = async (username: string, password: string) => {
    const res = await api.login(username, password)
    const claims = jwtDecode<AuthClaims>(res.token)
    setUser({ token: res.token, ...claims })
  }

  const logout = () => setUser(null)

  const value = useMemo(() => ({ user, login, logout }), [user])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
