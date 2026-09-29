import { useEffect, useState, type FormEvent } from 'react'
import { ApiError } from '../../api/client'
import type {
  Equipment,
  UnitOperation,
  UnitOperationPayload,
  UnitOpStatus,
  Violation,
} from '../../api/types'

type Props = {
  operation: UnitOperation | null
  equipment: Equipment[]
  open: boolean
  onClose: () => void
  onSave: (opId: number, payload: UnitOperationPayload) => Promise<Violation[]>
  onDelete: (opId: number) => Promise<void>
}

export function EditOperationDrawer({
  operation,
  equipment,
  open,
  onClose,
  onSave,
  onDelete,
}: Props) {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [equipmentId, setEquipmentId] = useState<number>(0)
  const [status, setStatus] = useState<UnitOpStatus>('draft')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [localViolations, setLocalViolations] = useState<Violation[]>([])

  useEffect(() => {
    if (!operation) return
    setStartDate(operation.start_date)
    setEndDate(operation.end_date)
    setEquipmentId(operation.equipment_id)
    setStatus(operation.status)
    setError(null)
    setLocalViolations([])
  }, [operation])

  if (!open || !operation) return null

  async function handleSave(event: FormEvent) {
    event.preventDefault()
    if (!operation) return
    setBusy(true)
    setError(null)
    try {
      const payload: UnitOperationPayload = {
        name: operation.name,
        type: operation.type,
        color: operation.color,
        status,
        start_date: startDate,
        end_date: endDate,
        batch_id: operation.batch_id,
        equipment_id: equipmentId,
      }
      const violations = await onSave(operation.id, payload)
      setLocalViolations(violations)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : 'Save failed')
      }
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete() {
    if (!operation) return
    if (!window.confirm(`Delete "${operation.name}"?`)) return
    setBusy(true)
    setError(null)
    try {
      await onDelete(operation.id)
      onClose()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : 'Delete failed')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="drawer-backdrop" role="presentation" onClick={onClose}>
      <aside
        className="drawer"
        role="dialog"
        aria-labelledby="edit-op-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="drawer-header">
          <h2 id="edit-op-title">Edit operation</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>

        <p className="drawer-meta">
          <strong>{operation.name}</strong> · {operation.type}
        </p>

        <form className="drawer-form" onSubmit={handleSave}>
          <label>
            Start date
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              required
            />
          </label>
          <label>
            End date (exclusive)
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              required
            />
          </label>
          <label>
            Equipment
            <select
              value={equipmentId}
              onChange={(e) => setEquipmentId(Number(e.target.value))}
            >
              {equipment.map((eq) => (
                <option key={eq.id} value={eq.id}>
                  {eq.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Status
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as UnitOpStatus)}
            >
              <option value="draft">draft</option>
              <option value="confirmed">confirmed</option>
              <option value="completed">completed</option>
            </select>
          </label>

          {error && <p className="form-error">{error}</p>}

          {localViolations.length > 0 && (
            <div className="drawer-violations">
              <h3>Current violations after save</h3>
              <ul>
                {localViolations.map((v, i) => (
                  <li key={`${v.rule_id}-${i}`}>
                    <strong>{v.rule_id}</strong> {v.message}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="drawer-actions">
            <button type="submit" disabled={busy}>
              {busy ? 'Saving…' : 'Save'}
            </button>
            <button
              type="button"
              className="danger"
              disabled={busy}
              onClick={handleDelete}
            >
              Delete
            </button>
          </div>
        </form>
      </aside>
    </div>
  )
}
