import { useCallback, useEffect, useState } from 'react'
import BookList from './components/library/BookList'
import BookReader from './components/reader/BookReader'
import { DEMO_BOOK } from './data/demoBook'

// Container de estado: biblioteca e navegação entre telas.
export default function App() {
  const [books, setBooks] = useState([])
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [data, setData] = useState(null)
  const [loadingBook, setLoadingBook] = useState(false)

  useEffect(() => {
    fetch('/books')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((list) => setBooks(list))
      .catch((e) => setError(e.message))
  }, [])

  const selectBook = useCallback(async (b) => {
    setSelected(b)
    setLoadingBook(true)
    setError('')
    try {
      const r = await fetch(b.jsonUrl)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      setData(await r.json())
    } catch (e) {
      setError(e.message)
      setSelected(null)
    } finally {
      setLoadingBook(false)
    }
  }, [])

  const selectDemo = useCallback(() => {
    setSelected({
      bookCode: DEMO_BOOK.bookCode,
      bookName: DEMO_BOOK.bookName,
      jsonUrl: null,
      audioUrl: null,
    })
    setData(DEMO_BOOK)
  }, [])

  const backToLibrary = useCallback(() => {
    setSelected(null)
    setData(null)
    setError('')
  }, [])

  if (loadingBook) {
    return <div className="app center">Carregando livro…</div>
  }

  if (selected && data) {
    return <BookReader data={data} audioUrl={selected.audioUrl} onBack={backToLibrary} />
  }

  return (
    <div className="app">
      <BookList books={books} error={error} onSelect={selectBook} onDemo={selectDemo} />
    </div>
  )
}
