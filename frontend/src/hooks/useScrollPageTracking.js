import { useEffect, useRef } from 'react'

// Rastreia a página "ativa" por rolagem (sem áudio): observa as seções de
// página e reporta via `onPageChange(index)` qual está mais próxima do centro
// da viewport. Requer que cada seção tenha `data-index` e que `sectionRefs`
// seja um array estável preenchido por refs.
export function useScrollPageTracking({ enabled, sectionRefs, onPageChange }) {
  const cbRef = useRef(onPageChange)
  cbRef.current = onPageChange
  const pageRef = useRef(-1)

  useEffect(() => {
    if (!enabled) return
    const observer = new IntersectionObserver(
      (entries) => {
        const vCenter = window.innerHeight / 2
        let best = null
        let bestDist = Infinity
        for (const e of entries) {
          if (!e.isIntersecting) continue
          const rect = e.target.getBoundingClientRect()
          const dist = Math.abs(rect.top + rect.height / 2 - vCenter)
          if (dist < bestDist) {
            bestDist = dist
            best = e
          }
        }
        if (best) {
          const i = Number(best.target.dataset.index)
          if (i !== pageRef.current) {
            pageRef.current = i
            cbRef.current(i)
          }
        }
      },
      { rootMargin: '-40% 0px -40% 0px' }
    )
    sectionRefs.current.forEach((el) => el && observer.observe(el))
    return () => observer.disconnect()
  }, [enabled, sectionRefs])
}
