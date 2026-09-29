import { useCallback, useEffect, useState } from 'react'
import {
  ApiError,
  deleteUnitOperation,
  fetchSchedule,
  updateUnitOperation,
} from '../api/client'
import type {
  ScheduleResponse,
  UnitOperation,
  UnitOperationPayload,
  Violation,
} from '../api/types'
import { DateRangeControls } from '../components/schedule/DateRangeControls'
import { EditOperationDrawer } from '../components/schedule/EditOperationDrawer'
import { GanttChart } from '../components/schedule/GanttChart'
import { ViolationsPanel } from '../components/schedule/ViolationsPanel'

const DEFAULT_START = '2025-10-01'
const DEFAULT_END = '2025-11-15'

export function SchedulePage() {
  const [startDate, setStartDate] = useState(DEFAULT_START)
  const [endDate, setEndDate] = useState(DEFAULT_END)
  const [appliedStart, setAppliedStart] = useState(DEFAULT_START)
  const [appliedEnd, setAppliedEnd] = useState(DEFAULT_END)
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<UnitOperation | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const load = useCallback(async (start: string, end: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchSchedule(start, end)
      setSchedule(data)
      setAppliedStart(start)
      setAppliedEnd(end)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load schedule. Is the backend running?',
        )
      }
      setSchedule(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load(DEFAULT_START, DEFAULT_END)
  }, [load])

  function handleSelect(op: UnitOperation) {
    setSelected(op)
    setDrawerOpen(true)
  }

  function handleSelectFromViolation(opId: number) {
    const op = schedule?.unit_operations.find((o) => o.id === opId)
    if (op) handleSelect(op)
  }

  async function handleSave(
    opId: number,
    payload: UnitOperationPayload,
  ): Promise<Violation[]> {
    const result = await updateUnitOperation(opId, payload)
    const refreshed = await fetchSchedule(appliedStart, appliedEnd)
    setSchedule(refreshed)
    const updated = refreshed.unit_operations.find((o) => o.id === opId)
    if (updated) setSelected(updated)
    return result.violations
  }

  async function handleDelete(opId: number) {
    await deleteUnitOperation(opId)
    setDrawerOpen(false)
    setSelected(null)
    await load(appliedStart, appliedEnd)
  }

  return (
    <div className="schedule-page">
      <header className="page-header">
        <div>
          <h1>Schedule</h1>
          <p className="lede">
            Equipment lanes with batch envelopes. Violations come from the
            backend.
          </p>
        </div>
        <DateRangeControls
          startDate={startDate}
          endDate={endDate}
          onChangeStart={setStartDate}
          onChangeEnd={setEndDate}
          onApply={() => void load(startDate, endDate)}
          loading={loading}
        />
      </header>

      {error && <div className="banner banner--error">{error}</div>}
      {loading && !schedule && <p className="muted">Loading schedule…</p>}

      {schedule && (
        <>
          {schedule.unit_operations.length === 0 ? (
            <p className="muted">No unit operations in this date range.</p>
          ) : (
            <GanttChart
              rangeStart={appliedStart}
              rangeEnd={appliedEnd}
              equipment={schedule.equipment}
              batches={schedule.batches}
              operations={schedule.unit_operations}
              violations={schedule.violations}
              onSelectOperation={handleSelect}
            />
          )}

          <ViolationsPanel
            violations={schedule.violations}
            onSelectOp={handleSelectFromViolation}
          />
        </>
      )}

      <EditOperationDrawer
        open={drawerOpen}
        operation={selected}
        equipment={schedule?.equipment ?? []}
        onClose={() => setDrawerOpen(false)}
        onSave={handleSave}
        onDelete={handleDelete}
      />
    </div>
  )
}
