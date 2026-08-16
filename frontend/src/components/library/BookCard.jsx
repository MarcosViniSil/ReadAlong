import Card from '../ui/Card'
import styles from './BookCard.module.css'

// Cartão clicável de um item da biblioteca.
export default function BookCard({ title, subtitle, onClick }) {
  return (
    <Card as="button" className={styles.card} onClick={onClick}>
      <span className={styles.title}>{title}</span>
      <span className={styles.subtitle}>{subtitle}</span>
    </Card>
  )
}
