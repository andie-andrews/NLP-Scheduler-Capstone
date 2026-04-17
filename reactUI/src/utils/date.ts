export const startOfWeekSunday = (date: Date): Date => {
  const d = new Date(date)
  const day = d.getDay()
  d.setDate(d.getDate() - day)
  d.setHours(0, 0, 0, 0)
  return d
}

export const addDays = (date: Date, days: number): Date => {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}

export const toIsoDate = (date: Date): string => date.toISOString().split('T')[0]

export const formatWeekLabel = (date: Date): string => date.toLocaleDateString(undefined, { month: 'short', day: '2-digit', year: 'numeric' })
