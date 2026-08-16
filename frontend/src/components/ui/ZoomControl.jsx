import { FONT_SCALES } from '../../constants'
import Button from './Button'
import styles from './ZoomControl.module.css'

// Controle de zoom de fonte reutilizável.
export default function ZoomControl({ scale, onChange, scales = FONT_SCALES }) {
  return (
    <div className={styles.group} role="group" aria-label="Controle de tamanho da fonte">
      {scales.map((s) => (
        <Button
          key={s}
          compact
          active={s === scale}
          aria-label={`Fonte ${s}x`}
          onClick={() => onChange(s)}
        >
          {s}x
        </Button>
      ))}
    </div>
  )
}
