import type { ReactNode } from 'react'
import { AppShell, Button, Divider, Group, NavLink, Stack, Text, Title } from '@mantine/core'
import { useAuth } from '../context/AuthContext'

export type ViewKey = 'my-schedule' | 'employees' | 'schedules' | 'assistant'

export function Layout({ activeView, onChangeView, children }: { activeView: ViewKey; onChangeView: (v: ViewKey)=>void; children: ReactNode }) {
  const { user, logout } = useAuth()
  const isManager = ['Supervisor', 'Manager'].includes(user?.role ?? '')

  return (
    <AppShell
      header={{ height: 64 }}
      navbar={{ width: 280, breakpoint: 'sm' }}
      padding='lg'
    >
      <AppShell.Header>
        <Group h='100%' px='md' justify='space-between'>
          <Title order={3}>Scheduler Pro</Title>
          <Text size='sm' c='dimmed'>
            {user?.fullName} ({user?.role})
          </Text>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p='md'>
        <Stack gap='xs'>
          <NavLink
            label='My Schedule'
            active={activeView === 'my-schedule'}
            onClick={() => onChangeView('my-schedule')}
          />
          {isManager && (
            <NavLink
              label='Manage Employees'
              active={activeView === 'employees'}
              onClick={() => onChangeView('employees')}
            />
          )}
          {isManager && (
            <NavLink
              label='Manage Schedules'
              active={activeView === 'schedules'}
              onClick={() => onChangeView('schedules')}
            />
          )}
          <NavLink
            label='AI Assistant'
            active={activeView === 'assistant'}
            onClick={() => onChangeView('assistant')}
          />
        </Stack>
        <Divider my='md' />
        <Button variant='light' color='red' onClick={logout}>
          Logout
        </Button>
      </AppShell.Navbar>

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  )
}
