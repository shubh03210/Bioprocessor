import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import {
  ApiError,
  createForecast,
  fetchControlState,
  fetchLatestForecast,
  postCommand,
  runControllerStep,
} from '../api/client'
import type { ControlCommand, ControlState, Forecast } from '../api/types'
import {
  ProcessChart,
  type ChartMarker,
  type SeriesPoint,
} from '../components/control/ProcessChart'

const POLL_MS = 2500
const ACTUATOR_LAG_H = 5 / 60
const STALE_FORECAST_H = 2 / 60

function seriesFor(state: ControlState | null, signal: string): SeriesPoint[] {
  if (!state) return []
  return state.readings
    .filter((r) => r.signal_name === signal)
    .map((r) => ({ t: r.time_h, v: r.value }))
    .sort((a, b) => a.t - b.t)
}

function forecastSeries(forecast: Forecast | null): SeriesPoint[] {
  if (!forecast) return []
  return forecast.points.map((p) => ({ t: p.target_time_h, v: p.value }))
}

function commandMarkers(commands: ControlCommand[]): ChartMarker[] {
  return commands.map((c) => ({
    t: c.apply_at_time_h,
    label: `${c.value}`,
    tone: c.status === 'rejected' ? 'reject' : 'ok',
  }))
}

export function ControlPage() {
  const [state, setState] = useState<ControlState | null>(null)
  const [forecast, setForecast] = useState<Forecast | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [setpoint, setSetpoint] = useState('8')
  const [submitMsg, setSubmitMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const next = await fetchControlState(2000)
      setState(next)
      setError(null)

      let latest = await fetchLatestForecast()
      const current = next.current_process_time_h
      const stale =
        latest == null ||
        (current != null &&
          latest.made_at_time_h < current - STALE_FORECAST_H)

      if (stale) {
        try {
          latest = await createForecast()
        } catch {
          // Need 60 min history — keep previous / null
        }
      }
      setForecast(latest)
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to load control state. Is the backend running?',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
    const id = window.setInterval(() => void refresh(), POLL_MS)
    return () => window.clearInterval(id)
  }, [refresh])

  const doSeries = useMemo(() => seriesFor(state, 'DO'), [state])
  const feedSeries = useMemo(() => seriesFor(state, 'feed_rate'), [state])
  const overlay = useMemo(() => forecastSeries(forecast), [forecast])
  const markers = useMemo(
    () => commandMarkers(state?.recent_commands ?? []),
    [state],
  )
  const rejected = useMemo(
    () =>
      (state?.recent_commands ?? [])
        .filter((c) => c.status === 'rejected')
        .slice()
        .reverse(),
    [state],
  )

  async function onSendSetpoint(e: FormEvent) {
    e.preventDefault()
    setSubmitMsg(null)
    const value = Number(setpoint)
    if (!Number.isFinite(value)) {
      setSubmitMsg('Enter a numeric feed rate.')
      return
    }
    const current = state?.current_process_time_h
    if (current == null) {
      setSubmitMsg('No process time yet — ingest readings first.')
      return
    }
    setBusy(true)
    try {
      const cmd = await postCommand({
        setpoint_name: 'feed_rate',
        value,
        unit: 'mL/h',
        apply_at_time_h: current + ACTUATOR_LAG_H,
        source: 'manual',
      })
      setSubmitMsg(
        `Accepted #${cmd.id} → ${cmd.value} mL/h at ${cmd.apply_at_time_h.toFixed(3)} h`,
      )
      await refresh()
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitMsg(`Rejected: ${err.message}`)
      } else {
        setSubmitMsg(err instanceof Error ? err.message : 'Command failed')
      }
      await refresh()
    } finally {
      setBusy(false)
    }
  }

  async function onControllerStep() {
    setBusy(true)
    setSubmitMsg(null)
    try {
      const result = await runControllerStep()
      setSubmitMsg(
        result.acted
          ? `Controller: ${result.reason}`
          : `Controller held: ${result.reason}`,
      )
      await refresh()
    } catch (err) {
      setSubmitMsg(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Controller step failed',
      )
    } finally {
      setBusy(false)
    }
  }

  const processTime =
    state?.current_process_time_h != null
      ? `${state.current_process_time_h.toFixed(3)} h`
      : '—'

  return (
    <div className="control-page">
      <header className="page-header control-header">
        <div>
          <h1>Live Control</h1>
          <p className="lede">
            Dissolved oxygen and feed traces with forecast overlay and command
            markers. Polls every {POLL_MS / 1000}s.
          </p>
        </div>
        <dl className="control-meta">
          <div>
            <dt>Process time</dt>
            <dd>{processTime}</dd>
          </div>
          <div>
            <dt>Readings</dt>
            <dd>{state?.reading_count ?? 0}</dd>
          </div>
          <div>
            <dt>Forecast</dt>
            <dd>
              {forecast
                ? `${forecast.model_version} @ ${forecast.made_at_time_h.toFixed(3)} h`
                : 'unavailable'}
            </dd>
          </div>
          <div>
            <dt>Link</dt>
            <dd className={error ? 'status-bad' : 'status-ok'}>
              {loading && !state ? 'loading…' : error ? 'error' : 'live'}
            </dd>
          </div>
        </dl>
      </header>

      {error ? <div className="banner error">{error}</div> : null}

      <ProcessChart
        title="Dissolved oxygen"
        yLabel="% DO"
        series={doSeries}
        overlay={overlay}
        markers={markers}
        yMin={0}
        yMax={100}
      />

      <ProcessChart
        title="Feed rate"
        yLabel="mL/h"
        series={feedSeries}
        markers={markers}
        yMin={0}
        yMax={30}
      />

      <section className="control-actions">
        <form className="setpoint-form" onSubmit={onSendSetpoint}>
          <label htmlFor="manual-setpoint">Manual feed setpoint (mL/h)</label>
          <div className="setpoint-row">
            <input
              id="manual-setpoint"
              type="number"
              min={0}
              max={30}
              step={0.1}
              value={setpoint}
              onChange={(e) => setSetpoint(e.target.value)}
              disabled={busy}
            />
            <button type="submit" disabled={busy}>
              Send
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => void onControllerStep()}
              disabled={busy}
            >
              Run controller step
            </button>
          </div>
          <p className="hint">
            Commands apply at process time + 5 min lag (0–30 mL/h). Rejects are
            stored and listed below.
          </p>
          {submitMsg ? <p className="submit-msg">{submitMsg}</p> : null}
        </form>

        <div className="rejects-panel">
          <h2>Rejected commands</h2>
          {rejected.length === 0 ? (
            <p className="muted">None yet.</p>
          ) : (
            <ul>
              {rejected.map((c) => (
                <li key={c.id}>
                  <span className="reject-time">
                    {c.apply_at_time_h.toFixed(3)} h
                  </span>{' '}
                  value {c.value} {c.unit} — {c.reject_reason ?? 'rejected'}
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  )
}
