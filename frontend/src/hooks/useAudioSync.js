import { useCallback, useEffect, useRef, useState } from 'react'

// Sincronização de áudio do leitor: expõe o estado de reprodução (tempo,
// duração, sentença ativa, tocando) e os controles (tocar/pausar, buscar),
// além das props para o elemento <audio>.
//
// `onPageChange(pageIndex)` é chamado quando a reprodução cruza uma fronteira
// de página. `scrollActive` habilita o auto-scroll da sentença ativa.
export function useAudioSync({ audioUrl, dataDuration, starts, flat, pages, onPageChange, scrollActive }) {
  const audioRef = useRef(null)
  const activeIdxRef = useRef(-1)
  const onPageChangeRef = useRef(onPageChange)
  onPageChangeRef.current = onPageChange

  const [time, setTime] = useState(0)
  const [duration, setDuration] = useState(dataDuration || 0)
  const [activeIdx, setActiveIdx] = useState(-1)
  const [playing, setPlaying] = useState(false)

  useEffect(() => {
    const a = audioRef.current
    if (!a) return
    const onLoaded = () => setDuration(a.duration || dataDuration || 0)
    a.addEventListener('loadedmetadata', onLoaded)
    return () => a.removeEventListener('loadedmetadata', onLoaded)
  }, [dataDuration])

  const handleTimeUpdate = useCallback(() => {
    const a = audioRef.current
    if (!a) return
    setTime(a.currentTime)
    if (!starts.length) return
    // Busca binária sobre os offsets globais das sentenças.
    let lo = 0
    let hi = starts.length - 1
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1
      if (starts[mid] <= a.currentTime) lo = mid
      else hi = mid - 1
    }
    const idx = lo
    if (idx !== activeIdxRef.current) {
      activeIdxRef.current = idx
      setActiveIdx(idx)
      const s = flat[idx]
      const p = pages.findIndex((pg) => pg.pageCode === s.pageCode)
      if (p !== -1) onPageChangeRef.current(p)
    }
  }, [starts, flat, pages])

  const seekTo = useCallback((t) => {
    const a = audioRef.current
    if (!a) return
    a.currentTime = Math.max(0, t)
    if (a.paused) {
      a.play()
      setPlaying(true)
    }
  }, [])

  const togglePlay = useCallback(() => {
    const a = audioRef.current
    if (!a) return
    if (a.paused) a.play()
    else a.pause()
  }, [])

  // Mantém a sentença ativa visível durante a reprodução.
  useEffect(() => {
    if (!scrollActive || activeIdx < 0) return
    document
      .getElementById(`sentence-${activeIdx}`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [activeIdx, scrollActive])

  const audioElementProps = {
    ref: audioRef,
    src: audioUrl,
    preload: 'metadata',
    onTimeUpdate: handleTimeUpdate,
    onPlay: () => setPlaying(true),
    onPause: () => setPlaying(false),
    onEnded: () => setPlaying(false),
  }

  return { audioElementProps, time, duration, activeIdx, playing, seekTo, togglePlay }
}
