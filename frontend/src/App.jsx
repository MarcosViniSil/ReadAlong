import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

const fmtTime = (t) => {
  if (t == null || !Number.isFinite(t)) return '00:00'
  const m = Math.floor(t / 60)
  const s = Math.floor(t % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

const TYPE_LABELS = {
  text: null,
  image: 'imagem',
  table: 'tabela',
  graphic: 'gráfico',
  latex: 'fórmula',
}

function BookList({ books, error, onSelect }) {
  if (error) return <p className="error">Não foi possível carregar os livros: {error}</p>
  if (books.length === 0) {
    return (
      <div className="empty">
        <p>Nenhum livro disponível ainda.</p>
        <p className="hint">Gere um áudio enviando um arquivo para <code>POST /books</code>.</p>
      </div>
    )
  }
  return (
    <ul className="book-list">
      {books.map((b) => (
        <li key={b.bookCode}>
          <button className="book-card" onClick={() => onSelect(b)}>
            <span className="book-title">{b.bookName}</span>
            <span className="book-meta">
              {b.pages} páginas · {fmtTime(b.duration)}
            </span>
          </button>
        </li>
      ))}
    </ul>
  )
}

function BookReader({ book, data, audioUrl, onBack }) {
  const audioRef = useRef(null)
  const [activeIdx, setActiveIdx] = useState(-1)
  const [pageIdx, setPageIdx] = useState(0)
  const [time, setTime] = useState(0)
  const [duration, setDuration] = useState(data.duration || 0)
  const sentenceRefs = useRef([])
  const activeIdxRef = useRef(-1)
  const pageIdxRef = useRef(0)

  const flat = useMemo(() => {
    const arr = []
    data.pages.forEach((page, pi) => {
      page.sentences.forEach((s) => arr.push({ ...s, pageIdx: pi }))
    })
    return arr
  }, [data])

  const starts = useMemo(() => flat.map((s) => s.start), [flat])

  const codeToIdx = useMemo(() => {
    const m = new Map()
    flat.forEach((s, i) => m.set(s.segmentCode, i))
    return m
  }, [flat])

  const syncActivePage = (idx) => {
    const s = flat[idx]
    if (!s) return
    if (s.pageIdx !== pageIdxRef.current) {
      pageIdxRef.current = s.pageIdx
      setPageIdx(s.pageIdx)
    }
  }

  const handleTimeUpdate = useCallback(() => {
    const t = audioRef.current?.currentTime ?? 0
    setTime(t)
    let lo = 0
    let hi = starts.length
    while (lo < hi) {
      const mid = (lo + hi) >> 1
      if (starts[mid] <= t) lo = mid + 1
      else hi = mid
    }
    const idx = lo - 1
    const active = idx >= 0 && t < flat[idx].end ? idx : -1
    if (active !== activeIdxRef.current) {
      activeIdxRef.current = active
      setActiveIdx(active)
    }
    syncActivePage(active)
  }, [flat, starts])

  // Scroll active sentence into view (only when it changes).
  useEffect(() => {
    if (activeIdx < 0) return
    sentenceRefs.current[activeIdx]?.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    })
  }, [activeIdx])

  useEffect(() => {
    const a = audioRef.current
    if (!a) return
    const onLoaded = () => setDuration(a.duration)
    a.addEventListener('loadedmetadata', onLoaded)
    return () => a.removeEventListener('loadedmetadata', onLoaded)
  }, [book])

  const seekTo = (idx) => {
    const a = audioRef.current
    if (!a) return
    a.currentTime = flat[idx].start
    if (a.paused) a.play()
  }

  const goToPage = (pi) => {
    if (pi < 0 || pi >= data.pages.length) return
    pageIdxRef.current = pi
    setPageIdx(pi)
    const sentences = data.pages[pi].sentences
    if (sentences.length && audioRef.current) {
      audioRef.current.currentTime = sentences[0].start
    }
  }

  const currentPage = data.pages[pageIdx]
  const pageLabel = data.pages.length > 1
    ? `Página ${pageIdx + 1} de ${data.pages.length}`
    : ''

  return (
    <div className="reader">
      <header className="reader-header">
        <button className="back" onClick={onBack}>← Biblioteca</button>
        <h1>{data.bookName}</h1>
        <span className="reader-meta">{pageLabel}</span>
      </header>

      <div className="player-bar">
        <audio
          ref={audioRef}
          src={audioUrl}
          controls
          preload="metadata"
          onTimeUpdate={handleTimeUpdate}
        />
        <div className="page-nav">
          <button onClick={() => goToPage(pageIdx - 1)} disabled={pageIdx === 0}>‹ Anterior</button>
          <button onClick={() => goToPage(pageIdx + 1)} disabled={pageIdx === data.pages.length - 1}>Próxima ›</button>
        </div>
      </div>

      <main className="content">
        {data.pages.map((page, pi) => (
          <section key={page.pageCode} className={pi === pageIdx ? 'page active' : 'page'}>
            <div className="page-code">{page.pageCode}</div>
            {page.sentences.map((s) => {
              const globalIdx = codeToIdx.get(s.segmentCode)
              const label = TYPE_LABELS[s.sentenceType]
              const cls = ['sentence']
              if (globalIdx === activeIdx) cls.push('highlight')
              return label ? (
                <span
                  key={s.segmentCode}
                  ref={(el) => (sentenceRefs.current[globalIdx] = el)}
                  className={`marker ${cls.join(' ')}`}
                >
                  [{label}]
                </span>
              ) : (
                <button
                  key={s.segmentCode}
                  ref={(el) => (sentenceRefs.current[globalIdx] = el)}
                  className={cls.join(' ')}
                  onClick={() => seekTo(globalIdx)}
                >
                  {s.text}
                </button>
              )
            })}
          </section>
        ))}
      </main>
    </div>
  )
}

export default function App() {
  const [books, setBooks] = useState([])
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)
  const [data, setData] = useState(null)
  const [loadingBook, setLoadingBook] = useState(false)

  useEffect(() => {
    fetch('/books')
      .then((r) => r.json())
      .then(setBooks)
      .catch((e) => setError(String(e)))
  }, [])

  const selectBook = async (b) => {
    setSelected(b)
    setLoadingBook(true)
    setData(null)
    try {
      const res = await fetch(b.jsonUrl)
      setData(await res.json())
    } catch (e) {
      setError(String(e))
    } finally {
      setLoadingBook(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>📖 ReadAlong</h1>
        <p className="tagline">Acompanhe a leitura com o áudio</p>
      </header>

      {!selected ? (
        <BookList books={books} error={error} onSelect={selectBook} />
      ) : loadingBook ? (
        <p className="loading">Carregando livro…</p>
      ) : data ? (
        <BookReader
          book={selected}
          data={data}
          audioUrl={selected.audioUrl}
          onBack={() => {
            setSelected(null)
            setData(null)
          }}
        />
      ) : (
        <p className="error">{error ?? 'Erro ao carregar o livro.'}</p>
      )}
    </div>
  )
}
