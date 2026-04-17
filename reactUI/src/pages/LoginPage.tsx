import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await login(username, password)
    } catch {
      setError('Invalid credentials.')
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <form onSubmit={onSubmit} style={{ width: 360, border: '1px solid #ddd', borderRadius: 8, padding: 20, display: 'grid', gap: 12 }}>
        <h1>Welcome to Scheduler Pro</h1>
        <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder='Username' />
        <input type='password' value={password} onChange={(e) => setPassword(e.target.value)} placeholder='Password' />
        {error && <p style={{ color: 'crimson' }}>{error}</p>}
        <button type='submit'>Login</button>
      </form>
    </div>
  )
}
