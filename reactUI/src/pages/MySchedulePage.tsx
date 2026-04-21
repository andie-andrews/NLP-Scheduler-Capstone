import { useEffect, useMemo, useState, useCallback } from 'react'
import { Badge, Button, Card, Grid, Group, Stack, Text, Title } from '@mantine/core'
import { api } from '../api/client'
import { PageWithAssistant } from '../components/PageWithAssistant'
import { useAuth } from '../context/AuthContext'
import { addDays, formatWeekLabel, startOfWeekSunday, toIsoDate } from '../utils/date'
import type { Shift } from '../types'

export function MySchedulePage() {
  const { user } = useAuth()
  const [weekOffset, setWeekOffset] = useState(0)
  const [shifts, setShifts] = useState<Shift[]>([])

  const weekStart = useMemo(() => addDays(startOfWeekSunday(new Date()), weekOffset * 7), [weekOffset])
  const weekEnd = useMemo(() => addDays(weekStart, 6), [weekStart])

  const loadShifts = useCallback(() => {
    if (!user) return
    api.getMySchedule(user.employeeId, user.token, toIsoDate(weekStart), toIsoDate(weekEnd)).then(setShifts).catch(() => setShifts([]))
  }, [user, weekStart, weekEnd])

  useEffect(() => {
    loadShifts()
  }, [loadShifts])

  const totalHours = shifts.reduce((acc, s) => acc + s.durationHours, 0)
  const weekDays = useMemo(() => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)), [weekStart])

  useEffect(() => {
    const handleShiftUpdate = () => {
      loadShifts()
    }
    const handleShiftCreate = () => {
      loadShifts()
    }

    window.addEventListener('shifts:updated', handleShiftUpdate)
    window.addEventListener('shifts:created', handleShiftCreate)

    return () => {
      window.removeEventListener('shifts:updated', handleShiftUpdate)
      window.removeEventListener('shifts:created', handleShiftCreate)
    }
  }, [loadShifts])

  const shiftsByDay = useMemo(() => {
    return weekDays.map((day) => {
      const dayKey = day.toDateString()
      const dayShifts = shifts
        .filter((shift) => new Date(shift.start).toDateString() === dayKey)
        .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
      return { day, dayShifts }
    })
  }, [shifts, weekDays])

  return (
    <PageWithAssistant>
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
        <Grid columns={7} gutter='sm'>
          {shiftsByDay.map(({ day, dayShifts }) => (
            <Grid.Col key={day.toISOString()} span={1}>
              <Card withBorder p='sm' h='100%'>
                <Stack gap='xs'>
                  <Text fw={700} size='sm'>
                    {day.toLocaleDateString(undefined, { weekday: 'short' })}
                  </Text>
                  <Text size='xs' c='dimmed'>
                    {day.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                  </Text>

                  {!dayShifts.length && (
                    <Text size='xs' c='dimmed'>
                      No shifts
                    </Text>
                  )}

                  {dayShifts.map((shift) => (
                    <Card key={shift.id} withBorder p='xs' radius='sm'>
                      <Stack gap={4}>
                        <Text size='xs' fw={600}>
                          {new Date(shift.start).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })}
                        </Text>
                        <Badge variant='light' size='sm'>
                          {shift.durationHours}h
                        </Badge>
                      </Stack>
                    </Card>
                  ))}
                </Stack>
              </Card>
            </Grid.Col>
          ))}
        </Grid>
      </Stack>
    </PageWithAssistant>
  )
}
