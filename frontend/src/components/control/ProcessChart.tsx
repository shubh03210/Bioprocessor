/** Lightweight SVG time-series chart for process-time traces. */

export type SeriesPoint = { t: number; v: number }

export type ChartMarker = {
  t: number
  label?: string
  tone?: 'ok' | 'reject' | 'neutral'
}

type Props = {
  title: string
  yLabel: string
  series: SeriesPoint[]
  overlay?: SeriesPoint[]
  overlayLabel?: string
  markers?: ChartMarker[]
  yMin?: number
  yMax?: number
  height?: number
}

function niceRange(min: number, max: number): [number, number] {
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) {
    return [min - 1, max + 1]
  }
  const pad = (max - min) * 0.08
  return [min - pad, max + pad]
}

function formatTime(h: number): string {
  if (h >= 10) return h.toFixed(1)
  if (h >= 1) return h.toFixed(2)
  return h.toFixed(3)
}

export function ProcessChart({
  title,
  yLabel,
  series,
  overlay,
  overlayLabel = 'Forecast',
  markers = [],
  yMin,
  yMax,
  height = 220,
}: Props) {
  const width = 920
  const pad = { top: 28, right: 16, bottom: 36, left: 48 }
  const innerW = width - pad.left - pad.right
  const innerH = height - pad.top - pad.bottom

  const allT = [
    ...series.map((p) => p.t),
    ...(overlay ?? []).map((p) => p.t),
    ...markers.map((m) => m.t),
  ]
  const allV = [
    ...series.map((p) => p.v),
    ...(overlay ?? []).map((p) => p.v),
  ]

  const tMin = allT.length ? Math.min(...allT) : 0
  const tMax = allT.length ? Math.max(...allT) : 1
  const [vLo, vHi] = niceRange(
    yMin ?? (allV.length ? Math.min(...allV) : 0),
    yMax ?? (allV.length ? Math.max(...allV) : 1),
  )

  const xScale = (t: number) =>
    pad.left + ((t - tMin) / Math.max(tMax - tMin, 1e-9)) * innerW
  const yScale = (v: number) =>
    pad.top + ((vHi - v) / Math.max(vHi - vLo, 1e-9)) * innerH

  const linePath = (pts: SeriesPoint[]) =>
    pts
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${xScale(p.t)} ${yScale(p.v)}`)
      .join(' ')

  const ticksX = 5
  const ticksY = 4

  return (
    <figure className="process-chart">
      <figcaption>
        <strong>{title}</strong>
        <span className="chart-unit">{yLabel}</span>
        {overlay && overlay.length > 0 ? (
          <span className="chart-legend forecast">{overlayLabel}</span>
        ) : null}
      </figcaption>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}>
        <rect
          x={pad.left}
          y={pad.top}
          width={innerW}
          height={innerH}
          className="chart-plot"
        />
        {Array.from({ length: ticksY + 1 }, (_, i) => {
          const v = vLo + ((vHi - vLo) * i) / ticksY
          const y = yScale(v)
          return (
            <g key={`y-${i}`}>
              <line
                x1={pad.left}
                x2={pad.left + innerW}
                y1={y}
                y2={y}
                className="chart-grid"
              />
              <text x={pad.left - 8} y={y + 4} className="chart-tick" textAnchor="end">
                {v.toFixed(1)}
              </text>
            </g>
          )
        })}
        {Array.from({ length: ticksX + 1 }, (_, i) => {
          const t = tMin + ((tMax - tMin) * i) / ticksX
          const x = xScale(t)
          return (
            <text
              key={`x-${i}`}
              x={x}
              y={height - 10}
              className="chart-tick"
              textAnchor="middle"
            >
              {formatTime(t)} h
            </text>
          )
        })}
        {series.length > 1 ? (
          <path d={linePath(series)} className="chart-series" fill="none" />
        ) : null}
        {overlay && overlay.length > 1 ? (
          <path
            d={linePath(overlay)}
            className="chart-overlay"
            fill="none"
          />
        ) : null}
        {markers.map((m) => {
          const x = xScale(m.t)
          const tone = m.tone ?? 'neutral'
          return (
            <g key={`m-${m.t}-${m.label ?? ''}`}>
              <line
                x1={x}
                x2={x}
                y1={pad.top}
                y2={pad.top + innerH}
                className={`chart-marker chart-marker-${tone}`}
              />
              <circle
                cx={x}
                cy={pad.top + 6}
                r={3.5}
                className={`chart-marker-dot chart-marker-${tone}`}
              />
            </g>
          )
        })}
      </svg>
    </figure>
  )
}
