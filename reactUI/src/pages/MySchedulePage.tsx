import { useEffect, useMemo, useState } from 'react'
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
    <section>
      <h2>My Schedule</h2>
      <button onClick={() => setWeekOffset((w) => w - 1)}>◀ Previous</button>
      <strong style={{ margin: '0 12px' }}>Week of {formatWeekLabel(weekStart)}</strong>
      <button onClick={() => setWeekOffset((w) => w + 1)}>Next ▶</button>
      <p>Total shifts: {shifts.length} | Total hours: {totalHours}</p>
      <ul>{shifts.map((s) => <li key={s.id}>{new Date(s.start).toLocaleString()} ({s.durationHours}h)</li>)}</ul>
    </section>
  )
}
