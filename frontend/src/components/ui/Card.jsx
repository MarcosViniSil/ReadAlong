import styles from './Card.module.css'

// Container básico com fundo de superfície, borda e cantos arredondados.
// `as` permite renderizar como outro elemento (ex.: botão de cartão).
export default function Card({ as: Tag = 'div', className, ...rest }) {
  return <Tag className={`${styles.card} ${className || ''}`} {...rest} />
}
