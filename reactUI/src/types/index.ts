export interface AuthClaims {
  employeeId: number
  role: string
  fullName: string
  firstName: string
  lastName: string
}

export interface Employee {
  id: number
  firstName: string
  lastName: string
  email: string
  roleId: number
}

export interface Schedule {
  id: number
  name: string
}

export interface Shift {
  id: number
  employeeId: number
  start: string
  durationHours: number
  scheduleId?: number
  scheduleName?: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  shiftData?: {
    id?: number
    start: string
    durationHours: number
  }
}
