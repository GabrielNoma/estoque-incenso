'use strict'

const fp = require('fastify-plugin')
const path = require('path')
const { urlDoBot } = require('../routes/pedidoBot')

// Plano gratuito do Render: o robô dorme e leva ~80 s para acordar. Ao abrir uma PÁGINA do estoque,
// avisamos o robô (GET /saude, rota pública, sem chave) sem esperar a resposta: quando a pessoa escolher o
// menu ele já está acordando. No máximo um aviso por intervalo (padrão 5 min).
const intervaloMs = () => (process.env.PEDIDO_BOT_ACORDAR_INTERVALO_MS === undefined
  ? 5 * 60 * 1000
  : Number(process.env.PEDIDO_BOT_ACORDAR_INTERVALO_MS))
const TEMPO_MAXIMO_MS = 120000

// Navegação de página: GET fora de /api e sem extensão de arquivo (/, /pedidos, ...).
function ehPagina(request) {
  if (request.method !== 'GET') return false
  const caminho = request.url.split('?')[0]
  return !caminho.startsWith('/api') && !path.extname(caminho)
}

async function acordarRoboPlugin(fastify) {
  let ultimoAviso = null // por instância do app: cada servidor controla o seu próprio intervalo

  fastify.addHook('onRequest', async (request) => {
    if (!ehPagina(request)) return
    const agora = Date.now()
    if (ultimoAviso !== null && agora - ultimoAviso < intervaloMs()) return
    ultimoAviso = agora
    // Sem await: a página nunca espera o robô e uma falha dele nunca chega ao usuário.
    fetch(`${urlDoBot()}/saude`, { signal: AbortSignal.timeout(TEMPO_MAXIMO_MS) })
      .catch((err) => request.log.debug({ operacao: 'acordar-robo', motivo: err.name }, 'Aviso ao robô não chegou'))
  })
}

module.exports = fp(acordarRoboPlugin, { name: 'acordar-robo' })
