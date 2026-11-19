'use strict'

const MENSAGEM_INDISPONIVEL = 'O serviço de pedidos não está disponível. Tente novamente em instantes.'
const MENSAGEM_ACESSO = 'O serviço de pedidos recusou o acesso. Avise o responsável: a chave do robô precisa ser conferida.'
const MENSAGEM_MUITAS = 'Muitas mensagens seguidas. Aguarde um instante e tente de novo.'
const LIMITE_CORPO_BYTES = 6 * 1024 * 1024
const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
const CABECALHOS_DE_DOWNLOAD = ['content-type', 'content-disposition']

// Lidos a cada chamada para permitir configuração por ambiente (e testes).
const urlDoBot = () => (process.env.PEDIDO_BOT_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')
const timeoutDoBot = () => Number(process.env.PEDIDO_BOT_TIMEOUT_MS) || 240000
// Chave do robô (escopos conversa e modelo): só do ambiente do servidor, nunca vai ao navegador nem ao log.
const chaveDoBot = () => process.env.PEDIDO_BOT_API_KEY || ''

class BotIndisponivelError extends Error {}
class BotAcessoRecusadoError extends Error {}
class BotLimiteError extends Error {}

// Única porta de saída para o robô: envia a chave, aplica timeout e traduz falha de rede e recusas de acesso.
async function chamarBot(caminho, opcoes = {}) {
  const controle = new AbortController()
  const temporizador = setTimeout(() => controle.abort(), timeoutDoBot())
  const headers = { ...(opcoes.headers || {}) }
  if (chaveDoBot()) headers.Authorization = `Bearer ${chaveDoBot()}`
  let resposta
  let corpo
  try {
    resposta = await fetch(`${urlDoBot()}${caminho}`, { ...opcoes, headers, signal: controle.signal })
    corpo = Buffer.from(await resposta.arrayBuffer())
  } catch (err) {
    throw new BotIndisponivelError(err.name)
  } finally {
    clearTimeout(temporizador)
  }
  // O corpo de erro do robô nunca chega à tela nestes casos: só um aviso em português.
  if (resposta.status === 401 || resposta.status === 403) throw new BotAcessoRecusadoError(String(resposta.status))
  if (resposta.status === 429) throw new BotLimiteError('429')
  return { status: resposta.status, headers: resposta.headers, corpo }
}

function repassar(reply, resposta) {
  for (const nome of CABECALHOS_DE_DOWNLOAD) {
    const valor = resposta.headers.get(nome)
    if (valor) reply.header(nome, valor)
  }
  return reply.code(resposta.status).send(resposta.corpo)
}

async function pedidoBotRoutes(fastify) {
  const parserBinario = (request, body, done) => done(null, body)
  fastify.addContentTypeParser('application/octet-stream', { parseAs: 'buffer', bodyLimit: LIMITE_CORPO_BYTES }, parserBinario)
  fastify.addContentTypeParser(XLSX_MIME, { parseAs: 'buffer', bodyLimit: LIMITE_CORPO_BYTES }, parserBinario)

  fastify.setErrorHandler((err, request, reply) => {
    if (err instanceof BotIndisponivelError) {
      // Sem texto de pedido nem id de conversa no log (privacidade).
      request.log.warn({ operacao: 'pedido-bot', motivo: err.message }, 'Robô de pedidos indisponível')
      return reply.code(503).send({ error: MENSAGEM_INDISPONIVEL })
    }
    if (err instanceof BotAcessoRecusadoError) {
      request.log.error({ operacao: 'pedido-bot', status: err.message }, 'Robô de pedidos recusou a chave')
      return reply.code(502).send({ error: MENSAGEM_ACESSO })
    }
    if (err instanceof BotLimiteError) {
      request.log.warn({ operacao: 'pedido-bot' }, 'Robô de pedidos limitou as requisições')
      return reply.code(429).send({ error: MENSAGEM_MUITAS })
    }
    if (err.statusCode && err.statusCode < 500) {
      return reply.code(err.statusCode).send({ error: err.message })
    }
    request.log.error({ operacao: 'pedido-bot', err: err.message }, 'Erro inesperado no proxy do robô')
    return reply.code(500).send({ error: 'Ocorreu um erro inesperado. Tente novamente.' })
  })

  // POST /api/pedido-bot/mensagem
  fastify.post('/pedido-bot/mensagem', async (request, reply) => {
    const { conversaId, texto } = request.body || {}
    if (typeof conversaId !== 'string' || !conversaId.trim() || typeof texto !== 'string' || !texto.trim()) {
      return reply.code(400).send({ error: 'Informe a conversa e a mensagem.' })
    }
    const resposta = await chamarBot('/api/mensagem', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ telefone: conversaId, texto }),
    })
    if (resposta.status !== 200) return repassar(reply, resposta)

    const dados = JSON.parse(resposta.corpo.toString('utf-8'))
    const idPedido = dados.arquivo?.url?.match(/\/pedidos\/(\d+)\/planilha/)?.[1]
    const arquivo = idPedido
      ? { nome: dados.arquivo.nome, url: `/api/pedido-bot/planilha/${idPedido}` }
      : null
    return { resposta: dados.resposta, arquivo }
  })

  // GET /api/pedido-bot/planilha/:id
  fastify.get('/pedido-bot/planilha/:id', async (request, reply) => {
    const { id } = request.params
    if (!/^\d+$/.test(id)) return reply.code(400).send({ error: 'Pedido inválido.' })
    return repassar(reply, await chamarBot(`/api/pedidos/${id}/planilha`))
  })

  // GET /api/pedido-bot/modelo
  fastify.get('/pedido-bot/modelo', async (request, reply) => repassar(reply, await chamarBot('/api/modelo')))

  // POST /api/pedido-bot/modelo
  fastify.post('/pedido-bot/modelo', { bodyLimit: LIMITE_CORPO_BYTES }, async (request, reply) => {
    const headers = { 'Content-Type': 'application/octet-stream' }
    const nome = request.headers['x-nome-arquivo']
    if (nome) headers['X-Nome-Arquivo'] = nome
    const resposta = await chamarBot('/api/modelo', { method: 'POST', headers, body: request.body })
    reply.header('content-type', 'application/json; charset=utf-8')
    return reply.code(resposta.status).send(resposta.corpo)
  })

  // GET /api/pedido-bot/modelo/info
  fastify.get('/pedido-bot/modelo/info', async (request, reply) => {
    const resposta = await chamarBot('/api/modelo/info')
    reply.header('content-type', 'application/json; charset=utf-8')
    return reply.code(resposta.status).send(resposta.corpo)
  })
}

module.exports = pedidoBotRoutes
