import { useEffect, useMemo, useState } from 'react'
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

  return (
    <section>
      <h2>Manage Schedules</h2>
      <button onClick={() => setWeekOffset((w) => w - 1)}>◀ Previous</button>
      <strong style={{ margin: '0 12px' }}>Week of {formatWeekLabel(weekStart)}</strong>
      <button onClick={() => setWeekOffset((w) => w + 1)}>Next ▶</button>
      <div>
        <select value={String(selectedScheduleId)} onChange={(e) => setSelectedScheduleId(e.target.value === 'all' ? 'all' : Number(e.target.value))}>
          <option value='all'>All Schedules</option>
          {schedules.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <input placeholder='Schedule name' value={nameDraft} onChange={(e) => setNameDraft(e.target.value)} />
        <button onClick={async () => user && api.createSchedule(user.token, nameDraft).then(load)}>Create</button>
        <button onClick={async () => selectedSchedule && user && api.updateSchedule(user.token, selectedSchedule.id, nameDraft).then(load)} disabled={!selectedSchedule}>Rename</button>
        <button onClick={async () => selectedSchedule && user && api.deleteSchedule(user.token, selectedSchedule.id).then(() => setSelectedScheduleId('all')).then(load)} disabled={!selectedSchedule}>Delete</button>
      </div>
      <p>Employees: {employees.length} | Shifts this week: {shifts.length}</p>
      <table><thead><tr><th>Employee</th><th>Shifts</th><th>Total Hours</th></tr></thead><tbody>
        {employees.map((employee) => {
          const employeeShifts = shifts.filter((s) => s.employeeId === employee.id)
          const totalHours = employeeShifts.reduce((acc, s) => acc + s.durationHours, 0)
          return <tr key={employee.id}><td>{employee.firstName} {employee.lastName}</td><td>{employeeShifts.length}</td><td>{totalHours}</td></tr>
        })}
      </tbody></table>
    </section>
  )
}
