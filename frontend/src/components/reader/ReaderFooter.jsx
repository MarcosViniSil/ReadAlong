import Row from '../ui/Row'
import ZoomControl from '../ui/ZoomControl'
import AudioControls from './AudioControls'
import styles from './ReaderFooter.module.css'

// Barra fixa inferior: controles de áudio (quando houver) e zoom de fonte.
export default function ReaderFooter({ hasAudio, playing, time, onTogglePlay, scale, onZoomChange }) {
  return (
    <footer className={styles.footer}>
      <Row between className={styles.inner}>
        {hasAudio && <AudioControls playing={playing} time={time} onToggle={onTogglePlay} />}
        <ZoomControl scale={scale} onChange={onZoomChange} />
      </Row>
    </footer>
  )
}
