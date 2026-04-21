import { useMemo } from 'react'
import { Badge, Card, Grid, Stack, Text } from '@mantine/core'
import { addDays } from '../utils/date'
import type { Shift } from '../types'

interface ScheduleCalendarProps {
  weekStart: Date
  shifts: Shift[]
}

export function ScheduleCalendar({ weekStart, shifts }: ScheduleCalendarProps) {
  const weekDays = useMemo(() => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)), [weekStart])

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
  )
}
