import { TYPE_LABELS } from '../../constants'
import styles from './PageSection.module.css'

// Uma página do livro: título centralizado e corpo em bloco único justificado,
// com sentenças clicáveis (read-along) e linha em destaque no final.
export default function PageSection({
  page,
  meta,
  pageNumber,
  active,
  activeIdx,
  codeToIdx,
  onSentenceClick,
  sectionRef,
}) {
  return (
    <section
      id={`page-${pageNumber}`}
      data-index={pageNumber}
      ref={sectionRef}
      className={`${styles.page} ${active ? styles.active : ''}`}
      aria-label={`Página ${pageNumber + 1}: ${meta.title}`}
    >
      <h2 className={styles.title}>{meta.title}</h2>
      <p className={styles.body}>
        {page.sentences.map((s, si) => {
          if (s === meta.titleSentence) return null
          const globalIdx = codeToIdx.get(s.segmentCode)
          const label = TYPE_LABELS[s.sentenceType]
          const cls = [styles.sentence, globalIdx === activeIdx ? styles.highlight : '']
            .filter(Boolean)
            .join(' ')
          return label ? (
            <span key={si} className={styles.marker}>
              [ {label} ]
            </span>
          ) : (
            <button
              key={si}
              id={`sentence-${globalIdx}`}
              className={cls}
              onClick={() => onSentenceClick(s)}
            >
              {s.text}
            </button>
          )
        })}
      </p>
      {meta.metaLine && (
        <em className={styles.metaLine} aria-label="Trecho de destaque">
          {meta.metaLine.text}
        </em>
      )}
    </section>
  )
}
