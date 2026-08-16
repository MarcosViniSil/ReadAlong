import Button from '../ui/Button'
import Row from '../ui/Row'
import styles from './BookHeader.module.css'

// Cabeçalho do livro: voltar/menu, autor, edição e progresso clicável que
// abre o popover de navegação por páginas (slider).
export default function BookHeader({
  author,
  edition,
  progressPct,
  menuOpen,
  onToggleMenu,
  onBack,
  navOpen,
  onToggleNav,
  pageIdx,
  totalPages,
  onSeekPage,
}) {
  return (
    <header className={styles.header}>
      <Row between gap={8} className={styles.topRow}>
        <Button variant="ghost" className={styles.back} onClick={onBack}>
          ← Biblioteca
        </Button>
        <Button
          variant="outlined"
          className={styles.menuToggle}
          aria-expanded={menuOpen}
          aria-label={menuOpen ? 'Fechar índice' : 'Abrir índice'}
          onClick={onToggleMenu}
        >
          ☰
        </Button>
      </Row>
      <p className={styles.author}>{author}</p>
      <Row between className={styles.subRow}>
        <p className={styles.edition}>{edition}</p>
        <Button
          variant="ghost"
          className={styles.progress}
          aria-expanded={navOpen}
          aria-label="Abrir navegação por páginas"
          onClick={onToggleNav}
        >
          {progressPct}%
        </Button>
      </Row>
      {navOpen && (
        <div className={styles.popover} role="dialog" aria-label="Navegação por páginas">
          <input
            type="range"
            min={1}
            max={Math.max(1, totalPages)}
            value={pageIdx + 1}
            aria-label="Página"
            onChange={(e) => onSeekPage(Number(e.target.value) - 1)}
          />
          <span className={styles.navLabel}>
            Página {pageIdx + 1} de {totalPages}
          </span>
        </div>
      )}
    </header>
  )
}
