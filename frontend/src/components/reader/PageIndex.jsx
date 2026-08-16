import Divider from '../ui/Divider'
import styles from './PageIndex.module.css'

// Índice de páginas: lista numerada com títulos; clique navega até a página.
// Em telas pequenas fica oculto até ser aberto pelo menu hambúrguer.
export default function PageIndex({ items, activeIndex, onSelect, open }) {
  return (
    <nav className={`${styles.index} ${open ? styles.open : ''}`} aria-label="Índice de páginas">
      <Divider />
      <ul>
        {items.map((m, i) => {
          const current = i === activeIndex
          return (
            <li key={i}>
              <button
                className={current ? `${styles.item} ${styles.current}` : styles.item}
                aria-current={current ? 'true' : undefined}
                onClick={() => onSelect(i)}
              >
                <span className={styles.num}>{String(i + 1).padStart(2, '0')}</span>
                <span className={styles.title}>{m.title}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
