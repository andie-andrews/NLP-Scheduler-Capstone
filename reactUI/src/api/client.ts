import type { Employee, Schedule, Shift } from '../types'

const schedulerBaseUrl = (import.meta.env.VITE_SCHEDULER_API_BASE_URL as string | undefined)?.replace(/\/$/, '')
  ?? 'https://nlp-scheduler-api-ehc5bhhdeparezd7.canadacentral-01.azurewebsites.net'

const employeeBaseUrl = (import.meta.env.VITE_EMPLOYEE_API_BASE_URL as string | undefined)?.replace(/\/$/, '')
  ?? 'https://nlp-employee-api.azurewebsites.net'

const buildHeaders = (token?: string) => {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}

async function request<T>(baseUrl: string, path: string, token?: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      ...buildHeaders(token),
      ...(init?.headers ?? {}),
    },
  })

  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status}: ${body || res.statusText}`)
  }

  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

const requestScheduler = <T>(path: string, token?: string, init?: RequestInit) =>
  request<T>(schedulerBaseUrl, path, token, init)

const requestEmployee = <T>(path: string, token?: string, init?: RequestInit) =>
  request<T>(employeeBaseUrl, path, token, init)

export const api = {
  login: (username: string, password: string) => requestScheduler<{ token: string }>('/api/auth/login', undefined, {
    method: 'POST', body: JSON.stringify({ username, password }),
  }),
  getMySchedule: (employeeId: number, token: string, startDate: string, endDate: string) =>
    requestEmployee<Shift[]>(`/api/employees/${employeeId}/shifts?startDate=${startDate}&endDate=${endDate}`, token),
  getEmployees: (token: string, query?: string) =>
    requestEmployee<Employee[]>(`/api/employees${query ? `?query=${encodeURIComponent(query)}` : ''}`, token),
  createEmployee: (token: string, payload: Pick<Employee, 'firstName'|'lastName'|'email'|'roleId'>) =>
    requestEmployee<Employee>('/api/employees', token, { method: 'POST', body: JSON.stringify(payload) }),
  updateEmployee: (token: string, id: number, payload: Pick<Employee, 'firstName'|'lastName'|'email'|'roleId'>) =>
    requestEmployee<void>(`/api/employees/${id}`, token, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteEmployee: (token: string, id: number) => requestEmployee<void>(`/api/employees/${id}`, token, { method: 'DELETE' }),
  getSchedules: (token: string) => requestScheduler<Schedule[]>('/api/schedules', token),
  createSchedule: (token: string, name: string) =>
    requestScheduler<Schedule>('/api/schedules', token, { method: 'POST', body: JSON.stringify({ name }) }),
  updateSchedule: (token: string, id: number, name: string) =>
    requestScheduler<void>(`/api/schedules/${id}`, token, { method: 'PUT', body: JSON.stringify({ name }) }),
  deleteSchedule: (token: string, id: number) => requestScheduler<void>(`/api/schedules/${id}`, token, { method: 'DELETE' }),
  getScheduleEmployees: (token: string, scheduleId: number) => requestScheduler<Employee[]>(`/api/schedules/${scheduleId}/scheduleEmployees`, token),
  addEmployeeToSchedule: (token: string, scheduleId: number, employeeId: number) =>
    requestScheduler<void>(`/api/schedules/${scheduleId}/scheduleEmployees/${employeeId}`, token, { method: 'POST' }),
  removeEmployeeFromSchedule: (token: string, scheduleId: number, employeeId: number) =>
    requestScheduler<void>(`/api/schedules/${scheduleId}/scheduleEmployees/${employeeId}`, token, { method: 'DELETE' }),
  getScheduleShifts: (token: string, scheduleId: number, startDate: string, endDate: string) =>
    requestScheduler<Shift[]>(`/api/schedules/${scheduleId}/shifts?startDate=${startDate}&endDate=${endDate}`, token),
  createShift: (token: string, scheduleId: number, employeeId: number, start: string, durationHours: number) =>
    requestScheduler<Shift>(`/api/schedules/${scheduleId}/shifts`, token, { method: 'POST', body: JSON.stringify({ employeeId, start, durationHours }) }),
  updateShift: (token: string, shiftId: number, start: string, durationHours: number) =>
    requestScheduler<void>(`/api/shifts/${shiftId}`, token, { method: 'PUT', body: JSON.stringify({ start, durationHours }) }),
  deleteShift: (token: string, shiftId: number) => requestScheduler<void>(`/api/shifts/${shiftId}`, token, { method: 'DELETE' }),
}
