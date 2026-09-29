import type { Batch, Equipment, UnitOperation, Violation } from '../../api/types'
import { daysBetween, eachDay } from '../../lib/dates'

const DAY_WIDTH = 32
const LANE_HEIGHT = 56
const LABEL_WIDTH = 88

type Props = {
  rangeStart: string
  rangeEnd: string
  equipment: Equipment[]
  batches: Batch[]
  operations: UnitOperation[]
  violations: Violation[]
  onSelectOperation: (op: UnitOperation) => void
}

function violationIds(violations: Violation[]): Set<number> {
  const ids = new Set<number>()
  for (const v of violations) {
    for (const id of v.operation_ids) ids.add(id)
  }
  return ids
}

function messagesForOp(violations: Violation[], opId: number): string[] {
  return violations
    .filter((v) => v.operation_ids.includes(opId))
    .map((v) => `${v.rule_id}: ${v.message}`)
}

export function GanttChart({
  rangeStart,
  rangeEnd,
  equipment,
  batches,
  operations,
  violations,
  onSelectOperation,
}: Props) {
  const days = eachDay(rangeStart, rangeEnd)
  const width = days.length * DAY_WIDTH
  const violating = violationIds(violations)
  const batchById = new Map(batches.map((b) => [b.id, b]))

  return (
    <div className="gantt-scroll">
      <div
        className="gantt"
        style={{
          ['--day-width' as string]: `${DAY_WIDTH}px`,
          ['--lane-height' as string]: `${LANE_HEIGHT}px`,
          ['--label-width' as string]: `${LABEL_WIDTH}px`,
        }}
      >
        <div className="gantt-header">
          <div className="gantt-corner">Equipment</div>
          <div className="gantt-axis" style={{ width }}>
            {days.map((day) => {
              const d = day.slice(8)
              const showMonth = day.endsWith('-01') || day === rangeStart
              return (
                <div key={day} className="gantt-tick" title={day}>
                  {showMonth ? day.slice(5) : d}
                </div>
              )
            })}
          </div>
        </div>

        {equipment.map((eq) => {
          const laneOps = operations.filter((op) => op.equipment_id === eq.id)
          const batchIdsOnLane = [...new Set(laneOps.map((op) => op.batch_id))]

          return (
            <div key={eq.id} className="gantt-lane">
              <div className="gantt-lane-label">{eq.name}</div>
              <div className="gantt-lane-track" style={{ width }}>
                {days.map((day) => (
                  <div key={day} className="gantt-cell" />
                ))}

                {batchIdsOnLane.map((batchId) => {
                  const batchOps = laneOps.filter((op) => op.batch_id === batchId)
                  if (batchOps.length === 0) return null
                  const starts = batchOps.map((op) => op.start_date)
                  const ends = batchOps.map((op) => op.end_date)
                  const envStart = starts.reduce((a, b) => (a < b ? a : b))
                  const envEnd = ends.reduce((a, b) => (a > b ? a : b))
                  const left = daysBetween(rangeStart, envStart) * DAY_WIDTH
                  const w = daysBetween(envStart, envEnd) * DAY_WIDTH
                  const batch = batchById.get(batchId)
                  return (
                    <div
                      key={`env-${batchId}`}
                      className="batch-envelope"
                      style={{ left, width: Math.max(w, DAY_WIDTH) }}
                      title={batch?.name ?? `Batch ${batchId}`}
                    >
                      <span className="batch-envelope-label">
                        {batch?.name ?? `Batch ${batchId}`}
                      </span>
                    </div>
                  )
                })}

                {laneOps.map((op) => {
                  const left = daysBetween(rangeStart, op.start_date) * DAY_WIDTH
                  const w = daysBetween(op.start_date, op.end_date) * DAY_WIDTH
                  const isBad = violating.has(op.id)
                  const tip = [
                    op.name,
                    `${op.type} · ${op.status}`,
                    `${op.start_date} → ${op.end_date}`,
                    ...messagesForOp(violations, op.id),
                  ].join('\n')

                  return (
                    <button
                      key={op.id}
                      type="button"
                      className={`op-block${isBad ? ' op-block--violation' : ''}`}
                      style={{
                        left,
                        width: Math.max(w, 8),
                        backgroundColor: op.color,
                      }}
                      title={tip}
                      onClick={() => onSelectOperation(op)}
                    >
                      <span className="op-block-name">
                        {isBad ? '⚠ ' : ''}
                        {op.name}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
