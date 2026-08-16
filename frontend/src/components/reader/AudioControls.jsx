import { fmtTime } from '../../utils/format'
import Button from '../ui/Button'
import styles from './AudioControls.module.css'

// Controles de reprodução discretos: play/pause e tempo decorrido.
export default function AudioControls({ playing, time, onToggle }) {
  return (
    <div className={styles.controls}>
      <Button
        variant="circle"
        aria-label={playing ? 'Pausar áudio' : 'Tocar áudio'}
        onClick={onToggle}
      >
        {playing ? '❚❚' : '▶'}
      </Button>
      <span className={styles.time}>{fmtTime(time)}</span>
    </div>
  )
}
