import type { Violation } from '../../api/types'

type Props = {
  violations: Violation[]
  onSelectOp?: (opId: number) => void
}

export function ViolationsPanel({ violations, onSelectOp }: Props) {
  if (violations.length === 0) {
    return (
      <aside className="violations-panel">
        <h2>Violations</h2>
        <p className="muted">No violations in this range.</p>
      </aside>
    )
  }

  return (
    <aside className="violations-panel">
      <h2>Violations ({violations.length})</h2>
      <ul>
        {violations.map((v, index) => (
          <li key={`${v.rule_id}-${v.operation_ids.join('-')}-${index}`}>
            <span className="rule-id">{v.rule_id}</span>
            <span>{v.message}</span>
            {onSelectOp && v.operation_ids[0] != null && (
              <button
                type="button"
                className="linkish"
                onClick={() => onSelectOp(v.operation_ids[0])}
              >
                View
              </button>
            )}
          </li>
        ))}
      </ul>
    </aside>
  )
}
