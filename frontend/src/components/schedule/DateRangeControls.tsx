import type { FormEvent } from 'react'

type Props = {
  startDate: string
  endDate: string
  onChangeStart: (value: string) => void
  onChangeEnd: (value: string) => void
  onApply: () => void
  loading?: boolean
}

export function DateRangeControls({
  startDate,
  endDate,
  onChangeStart,
  onChangeEnd,
  onApply,
  loading,
}: Props) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    onApply()
  }

  return (
    <form className="date-range" onSubmit={handleSubmit}>
      <label>
        Start
        <input
          type="date"
          value={startDate}
          onChange={(e) => onChangeStart(e.target.value)}
        />
      </label>
      <label>
        End (exclusive)
        <input
          type="date"
          value={endDate}
          onChange={(e) => onChangeEnd(e.target.value)}
        />
      </label>
      <button type="submit" disabled={loading}>
        {loading ? 'Loading…' : 'Go'}
      </button>
    </form>
  )
}
