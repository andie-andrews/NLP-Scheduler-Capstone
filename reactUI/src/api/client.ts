import type { Employee, Schedule, Shift } from '../types'

const BASE_URL = (import.meta.env.VITE_SCHEDULER_API_BASE_URL as string | undefined)?.replace(/\/$/, '')
  ?? 'https://nlp-scheduler-api-ehc5bhhdeparezd7.canadacentral-01.azurewebsites.net'

const buildHeaders = (token?: string) => {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}

async function request<T>(path: string, token?: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
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

export const api = {
  login: (username: string, password: string) => request<{ token: string }>('/api/auth/login', undefined, {
    method: 'POST', body: JSON.stringify({ username, password }),
  }),
  getMySchedule: (employeeId: number, token: string, startDate: string, endDate: string) =>
    request<Shift[]>(`/api/employees/${employeeId}/shifts?startDate=${startDate}&endDate=${endDate}`, token),
  getEmployees: (token: string, query?: string) => request<Employee[]>(`/api/employees${query ? `?query=${encodeURIComponent(query)}` : ''}`, token),
  createEmployee: (token: string, payload: Pick<Employee, 'firstName'|'lastName'|'email'|'roleId'>) =>
    request<Employee>('/api/employees', token, { method: 'POST', body: JSON.stringify(payload) }),
  updateEmployee: (token: string, id: number, payload: Pick<Employee, 'firstName'|'lastName'|'email'|'roleId'>) =>
    request<void>(`/api/employees/${id}`, token, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteEmployee: (token: string, id: number) => request<void>(`/api/employees/${id}`, token, { method: 'DELETE' }),
  getSchedules: (token: string) => request<Schedule[]>('/api/schedules', token),
  createSchedule: (token: string, name: string) => request<Schedule>('/api/schedules', token, { method: 'POST', body: JSON.stringify({ name }) }),
  updateSchedule: (token: string, id: number, name: string) => request<void>(`/api/schedules/${id}`, token, { method: 'PUT', body: JSON.stringify({ name }) }),
  deleteSchedule: (token: string, id: number) => request<void>(`/api/schedules/${id}`, token, { method: 'DELETE' }),
  getScheduleEmployees: (token: string, scheduleId: number) => request<Employee[]>(`/api/schedules/${scheduleId}/scheduleEmployees`, token),
  addEmployeeToSchedule: (token: string, scheduleId: number, employeeId: number) => request<void>(`/api/schedules/${scheduleId}/scheduleEmployees/${employeeId}`, token, { method: 'POST' }),
  removeEmployeeFromSchedule: (token: string, scheduleId: number, employeeId: number) => request<void>(`/api/schedules/${scheduleId}/scheduleEmployees/${employeeId}`, token, { method: 'DELETE' }),
  getScheduleShifts: (token: string, scheduleId: number, startDate: string, endDate: string) =>
    request<Shift[]>(`/api/schedules/${scheduleId}/shifts?startDate=${startDate}&endDate=${endDate}`, token),
  createShift: (token: string, scheduleId: number, employeeId: number, start: string, durationHours: number) =>
    request<Shift>(`/api/schedules/${scheduleId}/shifts`, token, { method: 'POST', body: JSON.stringify({ employeeId, start, durationHours }) }),
  updateShift: (token: string, shiftId: number, start: string, durationHours: number) =>
    request<void>(`/api/shifts/${shiftId}`, token, { method: 'PUT', body: JSON.stringify({ start, durationHours }) }),
  deleteShift: (token: string, shiftId: number) => request<void>(`/api/shifts/${shiftId}`, token, { method: 'DELETE' }),
}
