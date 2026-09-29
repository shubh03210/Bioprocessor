/** Types matching backend schedule API contracts. */

export type UnitOpType = 'Seed' | 'Bioreactor' | 'TFF' | 'Spray' | 'Sum'
export type UnitOpStatus = 'draft' | 'confirmed' | 'completed'

export type Equipment = {
  id: number
  name: string
}

export type Batch = {
  id: number
  name: string
  start_date: string
  end_date: string
}

export type UnitOperation = {
  id: number
  name: string
  type: UnitOpType
  color: string
  status: UnitOpStatus
  start_date: string
  end_date: string
  batch_id: number
  equipment_id: number
}

export type Dependency = {
  id: number
  from_unitop_id: number
  to_unitop_id: number
}

export type Violation = {
  rule_id: string
  message: string
  operation_ids: number[]
}

export type ScheduleResponse = {
  start_date: string
  end_date: string
  equipment: Equipment[]
  batches: Batch[]
  unit_operations: UnitOperation[]
  dependencies: Dependency[]
  violations: Violation[]
}

export type UnitOperationPayload = {
  name: string
  type: UnitOpType
  color: string
  status: UnitOpStatus
  start_date: string
  end_date: string
  batch_id: number
  equipment_id: number
}

export type MutationResult = {
  unit_operation: UnitOperation
  violations: Violation[]
}

export type ApiErrorBody = {
  error: {
    code: string
    message: string
    details?: unknown[]
  }
}

export type HealthResponse = {
  status: string
  service: string
  version: string
  environment: string
}

export type Reading = {
  id: number
  time_h: number
  signal_name: string
  value: number
  unit: string
  created_at: string
}

export type ControlCommand = {
  id: number
  setpoint_name: string
  value: number
  unit: string
  apply_at_time_h: number
  status: string
  reject_reason: string | null
  source: string | null
  created_at: string
}

export type ControlState = {
  current_process_time_h: number | null
  readings: Reading[]
  reading_count: number
  recent_commands: ControlCommand[]
}

export type ForecastPoint = {
  target_time_h: number
  value: number
}

export type Forecast = {
  made_at_time_h: number
  model_version: string
  points: ForecastPoint[]
}

export type CommandPayload = {
  setpoint_name: string
  value: number
  unit: string
  apply_at_time_h: number
  source?: 'manual' | 'controller'
}

export type ControllerStepResult = {
  acted: boolean
  reason: string
  command: ControlCommand | null
}
