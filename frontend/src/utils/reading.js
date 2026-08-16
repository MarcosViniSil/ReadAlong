// Heurísticas de leitura: detecção de título de página e derivação de metadata.

// Uma sentença parece um título se for curta, não terminar com pontuação de
// frase e começar com letra maiúscula (ex.: "Do Título", "CAPÍTULO I").
export function isHeadingSentence(s) {
  const t = (s?.text ?? '').trim()
  if (!t || t.length > 60) return false
  const words = t.split(/\s+/).length
  return words <= 8 && !/[.!?…]$/.test(t) && /^[A-ZÀ-Ú0-9]/.test(t)
}

// Metadata por página: título (primeira sentença quando parece heading, senão
// "Página N"), sentença usada como título (omitida do corpo) e linha em
// destaque ao final da página.
export function derivePageMeta(pages) {
  return pages.map((page, i) => {
    const first = page.sentences?.[0]
    const titleSentence = isHeadingSentence(first) ? first : null
    const title = titleSentence ? first.text : `Página ${i + 1}`
    const metaLine = page.sentences?.find((s) => s.emphasized) ?? null
    return { title, titleSentence, metaLine }
  })
}
