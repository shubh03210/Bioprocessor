/** Date helpers for exclusive-end schedule intervals (ISO YYYY-MM-DD). */

const MS_PER_DAY = 24 * 60 * 60 * 1000

export function parseISODate(value: string): Date {
  const [y, m, d] = value.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function formatISODate(value: Date): string {
  const y = value.getFullYear()
  const m = String(value.getMonth() + 1).padStart(2, '0')
  const d = String(value.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function daysBetween(startISO: string, endISO: string): number {
  const start = parseISODate(startISO)
  const end = parseISODate(endISO)
  return Math.round((end.getTime() - start.getTime()) / MS_PER_DAY)
}

export function addDays(iso: string, days: number): string {
  const d = parseISODate(iso)
  d.setDate(d.getDate() + days)
  return formatISODate(d)
}

export function eachDay(startISO: string, endISO: string): string[] {
  const days: string[] = []
  let cursor = startISO
  while (daysBetween(cursor, endISO) > 0) {
    days.push(cursor)
    cursor = addDays(cursor, 1)
  }
  return days
}
