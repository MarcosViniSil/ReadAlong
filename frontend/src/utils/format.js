// Formatação de valores para exibição.

export function fmtTime(t) {
  if (!Number.isFinite(t)) return '00:00'
  const s = Math.max(0, Math.floor(t))
  const m = Math.floor(s / 60)
  return `${String(m).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}
