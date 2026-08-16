import styles from './Divider.module.css'

// Linha horizontal divisória.
export default function Divider({ className, ...rest }) {
  return <hr className={`${styles.divider} ${className || ''}`} {...rest} />
}
