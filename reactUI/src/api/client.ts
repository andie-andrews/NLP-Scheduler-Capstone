import type { Employee, ScheduleGroup, Shift } from '../types'

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
  getScheduleGroups: (token: string) => requestScheduler<ScheduleGroup[]>('/api/schedule-groups', token),
  createScheduleGroup: (token: string, name: string) =>
    requestScheduler<ScheduleGroup>('/api/schedule-groups', token, { method: 'POST', body: JSON.stringify({ name }) }),
  updateScheduleGroup: (token: string, id: number, name: string) =>
    requestScheduler<void>(`/api/schedule-groups/${id}`, token, { method: 'PUT', body: JSON.stringify({ name }) }),
  deleteScheduleGroup: (token: string, id: number) => requestScheduler<void>(`/api/schedule-groups/${id}`, token, { method: 'DELETE' }),
  getScheduleGroupEmployees: (token: string, scheduleGroupId: number) => requestScheduler<Employee[]>(`/api/schedule-groups/${scheduleGroupId}/scheduleGroupEmployees`, token),
  addEmployeeToScheduleGroup: (token: string, scheduleGroupId: number, employeeId: number) =>
    requestScheduler<void>(`/api/schedule-groups/${scheduleGroupId}/scheduleGroupEmployees/${employeeId}`, token, { method: 'POST' }),
  removeEmployeeFromScheduleGroup: (token: string, scheduleGroupId: number, employeeId: number) =>
    requestScheduler<void>(`/api/schedule-groups/${scheduleGroupId}/scheduleGroupEmployees/${employeeId}`, token, { method: 'DELETE' }),
  getScheduleShifts: (token: string, scheduleGroupId: number, startDate: string, endDate: string) =>
    requestScheduler<Shift[]>(`/api/schedule-groups/${scheduleGroupId}/shifts?startDate=${startDate}&endDate=${endDate}`, token),
  createShift: (token: string, scheduleGroupId: number, employeeId: number, start: string, durationHours: number) =>
    requestScheduler<Shift>(`/api/schedule-groups/${scheduleGroupId}/shifts`, token, { method: 'POST', body: JSON.stringify({ employeeId, start, durationHours }) }),
  updateShift: (token: string, shiftId: number, start: string, durationHours: number) =>
    requestScheduler<void>(`/api/shifts/${shiftId}`, token, { method: 'PUT', body: JSON.stringify({ start, durationHours }) }),
  deleteShift: (token: string, shiftId: number) => requestScheduler<void>(`/api/shifts/${shiftId}`, token, { method: 'DELETE' }),
}
