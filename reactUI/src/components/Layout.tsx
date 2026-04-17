import type { ReactNode } from 'react'
import { useAuth } from '../context/AuthContext'

export type ViewKey = 'my-schedule' | 'employees' | 'schedules' | 'assistant'

export function Layout({ activeView, onChangeView, children }: { activeView: ViewKey; onChangeView: (v: ViewKey)=>void; children: ReactNode }) {
  const { user, logout } = useAuth()
  const isManager = ['Supervisor', 'Manager'].includes(user?.role ?? '')

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', minHeight: '100vh', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <aside style={{ borderRight: '1px solid #ddd', padding: 16 }}>
        <h2>📅 Scheduler Pro</h2>
        <p><strong>{user?.fullName}</strong><br/>{user?.role}</p>
        <nav style={{ display: 'grid', gap: 8 }}>
          <button onClick={() => onChangeView('my-schedule')}>My Schedule</button>
          {isManager && <button onClick={() => onChangeView('employees')}>Manage Employees</button>}
          {isManager && <button onClick={() => onChangeView('schedules')}>Manage Schedules</button>}
        </nav>
        <hr/>
        <button onClick={() => onChangeView('assistant')}>🤖 Open AI Assistant</button>
        <button onClick={logout} style={{ marginTop: 8 }}>Logout</button>
      </aside>
      <main style={{ padding: 24 }}>{children}</main>
    </div>
  )
}
