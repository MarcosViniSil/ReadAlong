import { useCallback, useMemo, useRef, useState } from 'react'
import { BASE_BODY_FONT_SIZE, FONT_SCALES, FONT_SCALE_KEY } from '../../constants'
import { derivePageMeta } from '../../utils/reading'
import { useAudioSync } from '../../hooks/useAudioSync'
import { useScrollPageTracking } from '../../hooks/useScrollPageTracking'
import { usePersistentState } from '../../hooks/usePersistentState'
import BookHeader from './BookHeader'
import PageIndex from './PageIndex'
import PageSection from './PageSection'
import ReaderFooter from './ReaderFooter'
import styles from './BookReader.module.css'

// Tela de leitura: cabeçalho, índice de páginas, conteúdo rolável e rodapé
// fixo com controles de áudio/zoom. Funciona com ou sem áudio.
export default function BookReader({ data, audioUrl, onBack }) {
  const pages = data.pages ?? []
  const hasAudio = Boolean(audioUrl)
  const sectionRefs = useRef([])

  const [pageIdx, setPageIdx] = useState(0)
  const [menuOpen, setMenuOpen] = useState(false)
  const [navOpen, setNavOpen] = useState(false)
  const [scale, setScale] = usePersistentState(
    FONT_SCALE_KEY,
    1,
    (v) => FONT_SCALES.includes(v)
  )

  // Sentenças achatadas com offsets globais, para busca binária por tempo.
  const flat = useMemo(() => {
    const arr = []
    pages.forEach((page) => {
      page.sentences.forEach((s) => arr.push({ ...s, pageCode: page.pageCode }))
    })
    return arr
  }, [pages])

  const starts = useMemo(() => flat.map((s) => s.start ?? 0), [flat])
  const codeToIdx = useMemo(() => {
    const m = new Map()
    flat.forEach((s, i) => m.set(s.segmentCode, i))
    return m
  }, [flat])

  const pageMeta = useMemo(() => derivePageMeta(pages), [pages])

  const { audioElementProps, time, duration, activeIdx, playing, seekTo, togglePlay } =
    useAudioSync({
      audioUrl,
      dataDuration: data.duration || 0,
      starts,
      flat,
      pages,
      onPageChange: setPageIdx,
      scrollActive: hasAudio,
    })

  // Sem áudio, a página ativa acompanha a rolagem.
  useScrollPageTracking({
    enabled: !hasAudio && pages.length > 0,
    sectionRefs,
    onPageChange: setPageIdx,
  })

  const progress = useMemo(() => {
    if (hasAudio && duration > 0) return Math.min(1, time / duration)
    return pages.length ? (pageIdx + 1) / pages.length : 0
  }, [hasAudio, duration, time, pageIdx, pages.length])

  const scrollToPage = useCallback((i) => {
    setNavOpen(false)
    setMenuOpen(false)
    document.getElementById(`page-${i}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [])

  const handleSentenceClick = useCallback(
    (s) => {
      if (!hasAudio) return
      const idx = codeToIdx.get(s.segmentCode)
      if (idx !== undefined) seekTo(s.start ?? 0)
    },
    [hasAudio, codeToIdx, seekTo]
  )

  return (
    <div className={styles.reader} style={{ '--body-size': `${BASE_BODY_FONT_SIZE * scale}px` }}>
      <BookHeader
        author={data.author || data.bookName}
        edition={data.edition || ''}
        progressPct={Math.round(progress * 100)}
        menuOpen={menuOpen}
        onToggleMenu={() => setMenuOpen((o) => !o)}
        onBack={onBack}
        navOpen={navOpen}
        onToggleNav={() => setNavOpen((o) => !o)}
        pageIdx={pageIdx}
        totalPages={pages.length}
        onSeekPage={scrollToPage}
      />

      <PageIndex items={pageMeta} activeIndex={pageIdx} onSelect={scrollToPage} open={menuOpen} />

      <main className={styles.content}>
        {pages.map((page, pi) => (
          <PageSection
            key={page.pageCode}
            page={page}
            meta={pageMeta[pi]}
            pageNumber={pi}
            active={pi === pageIdx}
            activeIdx={activeIdx}
            codeToIdx={codeToIdx}
            onSentenceClick={handleSentenceClick}
            sectionRef={(el) => (sectionRefs.current[pi] = el)}
          />
        ))}
      </main>

      <ReaderFooter
        hasAudio={hasAudio}
        playing={playing}
        time={time}
        onTogglePlay={togglePlay}
        scale={scale}
        onZoomChange={setScale}
      />

      {hasAudio && <audio hidden {...audioElementProps} />}
    </div>
  )
}
