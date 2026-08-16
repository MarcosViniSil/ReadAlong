import { useCallback, useState } from 'react'

// Estado persistido em localStorage. `validate` filtra valores inválidos
// (ex.: uma escala de fonte que não existe mais).
export function usePersistentState(key, initial, validate) {
  const [value, setValue] = useState(() => {
    const raw = localStorage.getItem(key)
    if (raw !== null) {
      const parsed = Number(raw)
      if (!validate || validate(parsed)) return parsed
    }
    return typeof initial === 'function' ? initial() : initial
  })

  const setPersisted = useCallback(
    (v) => {
      setValue(v)
      localStorage.setItem(key, String(v))
    },
    [key]
  )

  return [value, setPersisted]
}
