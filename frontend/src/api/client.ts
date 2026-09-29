import type {
  ApiErrorBody,
  CommandPayload,
  ControlCommand,
  ControllerStepResult,
  ControlState,
  Forecast,
  HealthResponse,
  MutationResult,
  ReplayStatus,
  ScheduleResponse,
  UnitOperationPayload,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export class ApiError extends Error {
  status: number
  code: string
  details: unknown[]

  constructor(status: number, body: ApiErrorBody) {
    super(body.error.message)
    this.status = status
    this.code = body.error.code
    this.details = body.error.details ?? []
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
    ...init,
  })

  if (response.status === 204) {
    return undefined as T
  }

  const data: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const body = data as ApiErrorBody | null
    if (body?.error) {
      throw new ApiError(response.status, body)
    }
    throw new Error(`HTTP ${response.status}`)
  }
  return data as T
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health')
}

export async function fetchSchedule(
  startDate: string,
  endDate: string,
): Promise<ScheduleResponse> {
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
  })
  return request<ScheduleResponse>(`/api/schedule?${params}`)
}

export async function updateUnitOperation(
  opId: number,
  payload: UnitOperationPayload,
): Promise<MutationResult> {
  return request<MutationResult>(`/api/unit_operations/${opId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function deleteUnitOperation(opId: number): Promise<void> {
  return request<void>(`/api/unit_operations/${opId}`, { method: 'DELETE' })
}

export async function fetchControlState(
  limit = 2000,
): Promise<ControlState> {
  return request<ControlState>(`/api/control/state?limit=${limit}`)
}

export async function fetchLatestForecast(): Promise<Forecast | null> {
  return request<Forecast | null>('/api/forecast/latest')
}

export async function createForecast(): Promise<Forecast> {
  return request<Forecast>('/api/forecast', { method: 'POST' })
}

export async function postCommand(
  payload: CommandPayload,
): Promise<ControlCommand> {
  return request<ControlCommand>('/command', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function runControllerStep(): Promise<ControllerStepResult> {
  return request<ControllerStepResult>('/api/control/step', { method: 'POST' })
}

export async function fetchReplayStatus(): Promise<ReplayStatus> {
  return request<ReplayStatus>('/api/control/replay')
}

export async function startReplay(
  runId: 'A' | 'B' | 'C',
  intervalS = 1,
): Promise<ReplayStatus> {
  return request<ReplayStatus>('/api/control/replay/start', {
    method: 'POST',
    body: JSON.stringify({ run_id: runId, interval_s: intervalS }),
  })
}

export async function stopReplay(): Promise<ReplayStatus> {
  return request<ReplayStatus>('/api/control/replay/stop', { method: 'POST' })
}

export async function cancelPendingCommands(): Promise<ControlCommand[]> {
  return request<ControlCommand[]>('/api/control/commands/cancel-pending', {
    method: 'POST',
  })
}
