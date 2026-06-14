export const STATUS_DRAFT = 'draft'
export const STATUS_APPROVED = 'approved'
export const STATUS_RECEIVED = 'received'
export const STATUS_COMPLETED = 'completed'
export const STATUS_CANCELLED = 'cancelled'

export const STATUS_LABELS = {
  [STATUS_DRAFT]: '草稿',
  [STATUS_APPROVED]: '已审批',
  [STATUS_RECEIVED]: '已到货',
  [STATUS_COMPLETED]: '已完成',
  [STATUS_CANCELLED]: '已取消'
}

export const STATUS_TRANSITIONS = {
  [STATUS_DRAFT]: [STATUS_APPROVED, STATUS_CANCELLED],
  [STATUS_APPROVED]: [STATUS_RECEIVED, STATUS_CANCELLED],
  [STATUS_RECEIVED]: [STATUS_COMPLETED],
  [STATUS_COMPLETED]: [],
  [STATUS_CANCELLED]: []
}

export const STATUS_NEXT_ACTIONS = {
  [STATUS_DRAFT]: '可审批或取消订单',
  [STATUS_APPROVED]: '可标记到货或取消订单',
  [STATUS_RECEIVED]: '可标记完成',
  [STATUS_COMPLETED]: '订单已完成，无法再变更状态',
  [STATUS_CANCELLED]: '订单已取消，无法再变更状态'
}

export const ALL_STATUSES = [
  STATUS_DRAFT,
  STATUS_APPROVED,
  STATUS_RECEIVED,
  STATUS_COMPLETED,
  STATUS_CANCELLED
]

export function getStatusLabel(status) {
  return STATUS_LABELS[status] || status
}

export function canTransition(currentStatus, targetStatus) {
  return STATUS_TRANSITIONS[currentStatus]?.includes(targetStatus) || false
}

export function getAvailableTransitions(currentStatus) {
  return STATUS_TRANSITIONS[currentStatus] || []
}

export function getNextActionsHint(currentStatus) {
  return STATUS_NEXT_ACTIONS[currentStatus] || '未知状态'
}
