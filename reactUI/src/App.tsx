import { useState } from 'react'
import { Layout, type ViewKey } from './components/Layout'
import { useAuth } from './context/AuthContext'
import { AIAssistantPage } from './pages/AIAssistantPage'
import { LoginPage } from './pages/LoginPage'
import { ManageEmployeesPage } from './pages/ManageEmployeesPage'
import { ManageSchedulesPage } from './pages/ManageSchedulesPage'
import { MySchedulePage } from './pages/MySchedulePage'

function renderView(view: ViewKey) {
  if (view === 'my-schedule') return <MySchedulePage />
  if (view === 'employees') return <ManageEmployeesPage />
  if (view === 'schedules') return <ManageSchedulesPage />
  return <AIAssistantPage />
}

export default function App() {
  const { user } = useAuth()
  const [activeView, setActiveView] = useState<ViewKey>('my-schedule')

  if (!user) return <LoginPage />

  return <Layout activeView={activeView} onChangeView={setActiveView}>{renderView(activeView)}</Layout>
}
