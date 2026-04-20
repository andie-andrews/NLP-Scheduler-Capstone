import { useEffect, useMemo, useState } from 'react'
import { Button, Card, Group, Select, Stack, Table, Text, TextInput, Title } from '@mantine/core'
import { api } from '../api/client'
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

  const selectedSchedule = schedules.find((s) => s.id === selectedScheduleId)
  const scheduleSelectData = [
    { value: 'all', label: 'All Schedules' },
    ...schedules.map((s) => ({ value: String(s.id), label: s.name })),
  ]

  return (
    <Stack>
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

      <Table striped highlightOnHover withTableBorder withColumnBorders>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Employee</Table.Th>
            <Table.Th>Shifts</Table.Th>
            <Table.Th>Total Hours</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {employees.map((employee) => {
            const employeeShifts = shifts.filter((s) => s.employeeId === employee.id)
            const totalHours = employeeShifts.reduce((acc, s) => acc + s.durationHours, 0)
            return (
              <Table.Tr key={employee.id}>
                <Table.Td>{employee.firstName} {employee.lastName}</Table.Td>
                <Table.Td>{employeeShifts.length}</Table.Td>
                <Table.Td>{totalHours}</Table.Td>
              </Table.Tr>
            )
          })}
        </Table.Tbody>
      </Table>
    </Stack>
  )
}
