import type { ReactNode } from 'react'
import { AppShell, Button, Divider, Group, Stack, Text, Title } from '@mantine/core'
import { useAuth } from '../context/AuthContext'

export type ViewKey = 'my-schedule' | 'employees' | 'schedules'

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
          <Button
            variant={activeView === 'my-schedule' ? 'filled' : 'outline'}
            color='black'
            autoContrast={true}
            radius={15}
            onClick={() => onChangeView('my-schedule')}
          >
            My Schedule
          </Button>
          {isManager && (
            <Button
              variant={activeView === 'employees' ? 'filled' : 'outline'}
              color='black'
              autoContrast={true}
              radius={15}
              onClick={() => onChangeView('employees')}
            >
              Manage Employees
            </Button>
          )}
          {isManager && (
            <Button
              variant={activeView === 'schedules' ? 'filled' : 'outline'}
              color='black'
              autoContrast={true}
              radius={15}
              onClick={() => onChangeView('schedules')}
            >
              Manage Schedule Groups
            </Button>
          )}
        </Stack>
        <Divider my='md' />
        <Button variant='light' color='red' onClick={logout} radius={15}>
          Logout
        </Button>
      </AppShell.Navbar>

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  )
}
