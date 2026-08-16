import styles from './Button.module.css'

// Botão base do sistema. Variantes: ghost (só texto), outlined (borda),
// circle (play), compact (zoom). `active` marca o estado pressionado
// (ex.: escala de fonte selecionada).
export default function Button({ variant = 'ghost', active = false, compact = false, className, ...rest }) {
  const cls = [
    styles.btn,
    styles[variant],
    compact ? styles.compact : '',
    active ? styles.active : '',
    className || '',
  ]
    .filter(Boolean)
    .join(' ')
  return <button type="button" className={cls} aria-pressed={active ? true : undefined} {...rest} />
}
