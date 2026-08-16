// Livro de demonstração: mesmo formato do JSON do backend, usado como
// fallback para validar a interface sem depender de um livro real.

function makeDemoPage(pageCode, title, body, metaLine) {
  const texts = metaLine ? [...body, metaLine] : body
  const sentences = [
    {
      sentenceType: 'text',
      text: title,
      segmentCode: `${pageCode}-S0`,
      nextSegmentCode: '',
      start: 0,
      end: 0,
      duration: 0,
    },
    ...texts.map((t, i) => ({
      sentenceType: 'text',
      text: t,
      segmentCode: `${pageCode}-S${i + 1}`,
      nextSegmentCode: '',
      start: 0,
      end: 0,
      duration: 0,
      ...(metaLine && i === texts.length - 1 ? { emphasized: true } : {}),
    })),
  ]
  return {
    pageCode,
    nextPageCode: '',
    start: 0,
    end: 0,
    sentences,
  }
}

export const DEMO_BOOK = {
  bookName: 'Memórias Póstumas de Brás Cubas',
  bookCode: 'demo-memorias',
  author: 'Machado de Assis',
  edition: '6 Carlos Mendes',
  audioFile: '',
  duration: 0,
  pages: [
    makeDemoPage(
      'P001',
      'Do Título',
      [
        'Alguns leitores hão de estranhar o título deste livro, e talvez perguntem por que começo por explicar aquilo que deveria ser claro.',
        'A verdade é que toda obra merece um título que a defina, e o meu, ainda que modesto, exprime exatamente o que se vai ler.',
        'Não é um capítulo longo, nem uma digressão; é apenas a chave que abre a porta do texto.',
      ],
      '“Agora que expliquei o título, passo a escrever o livro.”'
    ),
    makeDemoPage('P002', 'Do Livro', [
      'Falar de um livro é falar de uma criatura viva, que nasce, cresce e ganha leitores com o tempo.',
      'Este que ora apresento foi escrito sem pressa, ao sabor das ideias, como convém a quem não tem relógio diante da página.',
      'Se algumas linhas parecerem vagas, lembre-se o leitor de que a vida também o é.',
    ]),
    makeDemoPage('P003', 'A Denúncia', [
      'Há na história desta família um episódio que a memória guarda com certa amargura: a tal denúncia.',
      'Palavra dita em hora imprópria, repetida por vias tortas, e eis que um simples comentário se torna sentença.',
      'Não me compete julgar agora; cumpre apenas narrar o que os papéis antigos contam.',
    ]),
    makeDemoPage('P004', 'José Dias', [
      'José Dias é daquelas figuras que se instalam na casa sem nunca terem pedido licença.',
      'Dizia-se agregado, mas era, na verdade, o espelho da família: refletia tudo com o devido brilho e algum exagero.',
      'Seu nome atravessa estas páginas como atravessou a sala de jantar: sempre presente, sempre necessário.',
    ]),
  ],
}
