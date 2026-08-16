import { fmtTime } from '../../utils/format'
import BookCard from './BookCard'
import styles from './BookList.module.css'

export default function BookList({ books, error, onSelect, onDemo }) {
  return (
    <div className={styles.library}>
      <p className={styles.title}>Biblioteca</p>
      {error && (
        <p className={styles.message}>Não foi possível carregar os livros: {error}</p>
      )}
      {!error && books.length === 0 && (
        <p className={styles.message}>
          Nenhum livro disponível ainda. Gere um áudio via <code>POST /books</code> e
          recarregue.
        </p>
      )}
      <ul className={styles.list}>
        {books.map((b) => (
          <li key={b.bookCode}>
            <BookCard
              title={b.bookName}
              subtitle={b.duration > 0 ? `Áudio ${fmtTime(b.duration)}` : 'Sem áudio'}
              onClick={() => onSelect(b)}
            />
          </li>
        ))}
        <li>
          <BookCard
            title="Demonstração da interface"
            subtitle="Visualização estática do leitor (sem áudio)"
            onClick={onDemo}
          />
        </li>
      </ul>
    </div>
  )
}
