import { useState } from 'react'
import { Layout, type ViewKey } from './components/Layout'
import { useAuth } from './context/AuthContext'
import { LoginPage } from './pages/LoginPage'
import { ManageEmployeesPage } from './pages/ManageEmployeesPage'
import { ManageScheduleGroupsPage } from './pages/ManageScheduleGroupsPage'
import { MySchedulePage } from './pages/MySchedulePage'

function renderView(view: ViewKey) {
  if (view === 'my-schedule') return <MySchedulePage />
  if (view === 'employees') return <ManageEmployeesPage />
  return <ManageScheduleGroupsPage />
}

export default function App() {
  const { user } = useAuth()
  const [activeView, setActiveView] = useState<ViewKey>('my-schedule')

  if (!user) return <LoginPage />

  return <Layout activeView={activeView} onChangeView={setActiveView}>{renderView(activeView)}</Layout>
}
