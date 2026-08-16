import styles from './Row.module.css'

// Linha flexível: `between` distribui os filhos com espaço entre eles;
// `gap` controla o espaçamento (px).
export default function Row({ between = false, gap, className, ...rest }) {
  const cls = [styles.row, between ? styles.between : '', className || '']
    .filter(Boolean)
    .join(' ')
  return <div className={cls} style={gap != null ? { gap } : undefined} {...rest} />
}
