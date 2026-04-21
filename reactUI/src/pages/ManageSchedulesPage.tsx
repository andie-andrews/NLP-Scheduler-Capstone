import { useEffect, useMemo, useState } from 'react'
import { Button, Card, Grid, Group, Select, Stack, Text, TextInput, Title } from '@mantine/core'
import { api } from '../api/client'
import { PageWithAssistant } from '../components/PageWithAssistant'
import { ScheduleCalendar } from '../components/ScheduleCalendar'
import { useAuth } from '../context/AuthContext'
import type { Employee, Schedule, Shift } from '../types'
import { addDays, formatWeekLabel, startOfWeekSunday, toIsoDate } from '../utils/date'

export function ManageSchedulesPage() {
  const { user } = useAuth()
  const [weekOffset, setWeekOffset] = useState(0)
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [selectedScheduleId, setSelectedScheduleId] = useState<number | 'all'>('all')
  const [employees, setEmployees] = useState<Employee[]>([])
  const [shifts, setShifts] = useState<Shift[]>([])
  const [nameDraft, setNameDraft] = useState('')

  const weekStart = useMemo(() => addDays(startOfWeekSunday(new Date()), weekOffset * 7), [weekOffset])
  const weekEnd = useMemo(() => addDays(weekStart, 6), [weekStart])

  const load = async () => {
    if (!user) return
    const sc = await api.getSchedules(user.token)
    setSchedules(sc)
    const allEmployees = await api.getEmployees(user.token)

    if (selectedScheduleId === 'all') {
      setEmployees(allEmployees)
      const allShifts = await Promise.all(sc.map(async (s) => {
        const list = await api.getScheduleShifts(user.token, s.id, toIsoDate(weekStart), toIsoDate(weekEnd))
        return list.map((shift) => ({ ...shift, scheduleId: s.id, scheduleName: s.name }))
      }))
      setShifts(allShifts.flat())
      return
    }

    setEmployees(await api.getScheduleEmployees(user.token, selectedScheduleId))
    setShifts(await api.getScheduleShifts(user.token, selectedScheduleId, toIsoDate(weekStart), toIsoDate(weekEnd)))
  }

  useEffect(() => { load().catch(() => undefined) }, [user, selectedScheduleId, weekOffset])

  useEffect(() => {
    const handleShiftChange = () => {
      load().catch(() => undefined)
    }

    window.addEventListener('shifts:updated', handleShiftChange)
    window.addEventListener('shifts:created', handleShiftChange)

    return () => {
      window.removeEventListener('shifts:updated', handleShiftChange)
      window.removeEventListener('shifts:created', handleShiftChange)
    }
  }, [user, selectedScheduleId, weekOffset])

  const selectedSchedule = schedules.find((s) => s.id === selectedScheduleId)
  const scheduleSelectData = [
    { value: 'all', label: 'All Schedules' },
    ...schedules.map((s) => ({ value: String(s.id), label: s.name })),
  ]

  return (
    <PageWithAssistant>
      <Stack style={{ height: '100%', minHeight: 0, flex: 1, overflow: 'hidden' }}>
        <Title order={2}>Manage Schedules</Title>

        <Group>
          <Button variant='light' onClick={() => setWeekOffset((w) => w - 1)}>Previous</Button>
          <Text fw={600}>Week of {formatWeekLabel(weekStart)}</Text>
          <Button variant='light' onClick={() => setWeekOffset((w) => w + 1)}>Next</Button>
        </Group>

        <Group align='end'>
          <Select
            label='Schedule'
            data={scheduleSelectData}
            value={String(selectedScheduleId)}
            onChange={(value) => setSelectedScheduleId(value === 'all' ? 'all' : Number(value))}
            allowDeselect={false}
            style={{ minWidth: 220 }}
          />
          <TextInput
            label='Schedule name'
            placeholder='Schedule name'
            value={nameDraft}
            onChange={(e) => setNameDraft(e.currentTarget.value)}
          />
          <Button onClick={async () => user && api.createSchedule(user.token, nameDraft).then(load)}>
            Create
          </Button>
          <Button
            variant='light'
            onClick={async () => selectedSchedule && user && api.updateSchedule(user.token, selectedSchedule.id, nameDraft).then(load)}
            disabled={!selectedSchedule}
          >
            Rename
          </Button>
          <Button
            color='red'
            variant='light'
            onClick={async () => selectedSchedule && user && api.deleteSchedule(user.token, selectedSchedule.id).then(() => setSelectedScheduleId('all')).then(load)}
            disabled={!selectedSchedule}
          >
            Delete
          </Button>
        </Group>

        <Card withBorder>
          <Text>Employees: {employees.length} | Shifts this week: {shifts.length}</Text>
        </Card>

        <Card withBorder p='xs' style={{ height: 'calc(100vh - 330px)', minHeight: 260, overflowY: 'auto' }}>
          <Stack gap='md'>
            {employees.map((employee) => {
              const employeeShifts = shifts.filter((s) => s.employeeId === employee.id)
              const totalHours = employeeShifts.reduce((acc, s) => acc + s.durationHours, 0)
              return (
                <Grid key={employee.id} gutter='sm' align='stretch'>
                  <Grid.Col span={3}>
                    <Card withBorder p='sm' h='100%'>
                      <Stack gap={4}>
                        <Text fw={700}>
                          {employee.firstName} {employee.lastName}
                        </Text>
                        <Text size='xs' c='dimmed'>
                          Shifts: {employeeShifts.length}
                        </Text>
                        <Text size='xs' c='dimmed'>
                          Total hours: {totalHours}
                        </Text>
                      </Stack>
                    </Card>
                  </Grid.Col>
                  <Grid.Col span={9}>
                    <ScheduleCalendar weekStart={weekStart} shifts={employeeShifts} />
                  </Grid.Col>
                </Grid>
              )
            })}
          </Stack>
        </Card>
      </Stack>
    </PageWithAssistant>
  )
}
