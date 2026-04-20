import { useEffect, useMemo, useState } from 'react'
import { Button, Card, Group, List, Stack, Text, Title } from '@mantine/core'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { addDays, formatWeekLabel, startOfWeekSunday, toIsoDate } from '../utils/date'
import type { Shift } from '../types'

export function MySchedulePage() {
  const { user } = useAuth()
  const [weekOffset, setWeekOffset] = useState(0)
  const [shifts, setShifts] = useState<Shift[]>([])

  const weekStart = useMemo(() => addDays(startOfWeekSunday(new Date()), weekOffset * 7), [weekOffset])
  const weekEnd = useMemo(() => addDays(weekStart, 6), [weekStart])

  useEffect(() => {
    if (!user) return
    api.getMySchedule(user.employeeId, user.token, toIsoDate(weekStart), toIsoDate(weekEnd)).then(setShifts).catch(() => setShifts([]))
  }, [user, weekStart, weekEnd])

  const totalHours = shifts.reduce((acc, s) => acc + s.durationHours, 0)

  return (
    <Stack>
      <Title order={2}>My Schedule</Title>
      <Group>
        <Button variant='light' onClick={() => setWeekOffset((w) => w - 1)}>
          Previous
        </Button>
        <Text fw={600}>Week of {formatWeekLabel(weekStart)}</Text>
        <Button variant='light' onClick={() => setWeekOffset((w) => w + 1)}>
          Next
        </Button>
      </Group>
      <Card withBorder>
        <Text>
          Total shifts: {shifts.length} | Total hours: {totalHours}
        </Text>
      </Card>
      <List spacing='xs'>
        {shifts.map((s) => (
          <List.Item key={s.id}>
            {new Date(s.start).toLocaleString()} ({s.durationHours}h)
          </List.Item>
        ))}
      </List>
    </Stack>
  )
}
