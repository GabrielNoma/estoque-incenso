'use strict'

const { test, before, after } = require('node:test')
const assert = require('node:assert/strict')
const http = require('node:http')
const { buildTestApp } = require('./helpers')

const MSG_INDISPONIVEL = 'O serviço de pedidos não está disponível. Tente novamente em instantes.'
const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

let app
let bot
let recebido // última requisição vista pelo robô falso
let comportamento = {}

function lerCorpo(req) {
  return new Promise((resolve) => {
    const partes = []
    req.on('data', (p) => partes.push(p))
    req.on('end', () => resolve(Buffer.concat(partes)))
  })
}

function enviarJson(res, status, obj) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' })
  res.end(JSON.stringify(obj))
}

async function tratarBot(req, res) {
  const corpo = await lerCorpo(req)
  recebido = { method: req.method, url: req.url, headers: req.headers, corpo }
  if (comportamento.demora) await new Promise((r) => setTimeout(r, comportamento.demora))
  if (comportamento.status) return enviarJson(res, comportamento.status, comportamento.json)

  if (req.method === 'POST' && req.url === '/api/mensagem') {
    return enviarJson(res, 200, {
      resposta: 'Pedido ok\nok ou não?',
      arquivo: comportamento.arquivo ?? null,
    })
  }
  if (req.method === 'GET' && /^\/api\/pedidos\/\d+\/planilha$/.test(req.url)) {
    res.writeHead(200, {
      'Content-Type': XLSX_MIME,
      'Content-Disposition': 'attachment; filename="pedido-12.xlsx"',
    })
    return res.end(Buffer.from('PLANILHA'))
  }
  if (req.method === 'GET' && req.url === '/api/modelo') {
    res.writeHead(200, {
      'Content-Type': XLSX_MIME,
      'Content-Disposition': 'attachment; filename="modelo-pedido.xlsx"',
    })
    return res.end(Buffer.from('MODELO'))
  }
  if (req.method === 'POST' && req.url === '/api/modelo') {
    return enviarJson(res, 200, {
      versao: 3, arquivo: 'novo.xlsx', produtos: 10,
      adicionados: ['X'], removidos: [], renomeados: [], apelidos_desativados: 0,
    })
  }
  if (req.method === 'GET' && req.url === '/api/modelo/info') {
    return enviarJson(res, 200, { versao: 2, arquivo: 'a.xlsx', produtos: 9, ativado_em: '2026-01-01' })
  }
  enviarJson(res, 404, { erro: 'nao_encontrado', mensagem: 'não encontrado' })
}

before(async () => {
  bot = http.createServer((req, res) => { tratarBot(req, res) })
  await new Promise((r) => bot.listen(0, '127.0.0.1', r))
  process.env.PEDIDO_BOT_URL = `http://127.0.0.1:${bot.address().port}`
  process.env.PEDIDO_BOT_TIMEOUT_MS = '90000'
  app = await buildTestApp()
})

after(async () => {
  await app.close()
  await new Promise((r) => bot.close(r))
})

test.beforeEach(() => { comportamento = {}; recebido = null })

test('POST /mensagem encaminha telefone/texto e devolve resposta sem arquivo', async () => {
  const res = await app.inject({
    method: 'POST', url: '/api/pedido-bot/mensagem',
    payload: { conversaId: 'abc-123', texto: '2 dz abre caminho' },
  })
  assert.equal(res.statusCode, 200)
  assert.deepEqual(res.json(), { resposta: 'Pedido ok\nok ou não?', arquivo: null })
  assert.equal(recebido.url, '/api/mensagem')
  assert.deepEqual(JSON.parse(recebido.corpo.toString()), { telefone: 'abc-123', texto: '2 dz abre caminho' })
})

test('POST /mensagem reescreve a url do arquivo', async () => {
  comportamento.arquivo = { nome: 'pedido-12.xlsx', url: '/api/pedidos/12/planilha' }
  const res = await app.inject({
    method: 'POST', url: '/api/pedido-bot/mensagem',
    payload: { conversaId: 'c', texto: 'ok' },
  })
  assert.deepEqual(res.json().arquivo, { nome: 'pedido-12.xlsx', url: '/api/pedido-bot/planilha/12' })
})

test('POST /mensagem sem conversaId ou texto responde 400', async () => {
  const res = await app.inject({ method: 'POST', url: '/api/pedido-bot/mensagem', payload: { texto: 'x' } })
  assert.equal(res.statusCode, 400)
  assert.ok(res.json().error)
  assert.equal(recebido, null)
})

test('GET /planilha/:id devolve o xlsx com Content-Disposition', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/pedido-bot/planilha/12' })
  assert.equal(res.statusCode, 200)
  assert.equal(res.rawPayload.toString(), 'PLANILHA')
  assert.match(res.headers['content-disposition'], /pedido-12\.xlsx/)
  assert.equal(recebido.url, '/api/pedidos/12/planilha')
})

test('GET /planilha/:id com id inválido responde 400 sem chamar o robô', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/pedido-bot/planilha/abc' })
  assert.equal(res.statusCode, 400)
  assert.equal(recebido, null)
})

test('GET /planilha/:id repassa erro 409 do robô', async () => {
  comportamento = { status: 409, json: { erro: 'pedido_nao_confirmado', mensagem: 'Pedido não confirmado.' } }
  const res = await app.inject({ method: 'GET', url: '/api/pedido-bot/planilha/12' })
  assert.equal(res.statusCode, 409)
  assert.equal(res.json().mensagem, 'Pedido não confirmado.')
})

test('GET /modelo devolve o download do modelo', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/pedido-bot/modelo' })
  assert.equal(res.statusCode, 200)
  assert.equal(res.rawPayload.toString(), 'MODELO')
  assert.match(res.headers['content-disposition'], /modelo-pedido\.xlsx/)
})

test('POST /modelo encaminha o corpo bruto e o X-Nome-Arquivo', async () => {
  const bytes = Buffer.from([0x50, 0x4b, 0x03, 0x04, 0xff, 0x00, 0x10])
  const res = await app.inject({
    method: 'POST', url: '/api/pedido-bot/modelo', payload: bytes,
    headers: { 'content-type': 'application/octet-stream', 'x-nome-arquivo': 'Modelo%20Novo.xlsx' },
  })
  assert.equal(res.statusCode, 200)
  assert.equal(res.json().versao, 3)
  assert.equal(recebido.url, '/api/modelo')
  assert.deepEqual(recebido.corpo, bytes)
  assert.equal(recebido.headers['x-nome-arquivo'], 'Modelo%20Novo.xlsx')
  assert.equal(recebido.headers['content-type'], 'application/octet-stream')
})

test('POST /modelo aceita o mime type do xlsx', async () => {
  const res = await app.inject({
    method: 'POST', url: '/api/pedido-bot/modelo', payload: Buffer.from('abc'),
    headers: { 'content-type': XLSX_MIME },
  })
  assert.equal(res.statusCode, 200)
  assert.equal(recebido.corpo.toString(), 'abc')
})

test('POST /modelo repassa 422 com a mensagem inalterada', async () => {
  const corpo = { erro: 'modelo_invalido', mensagem: 'Modelo inválido: confira o modelo.' }
  comportamento = { status: 422, json: corpo }
  const res = await app.inject({
    method: 'POST', url: '/api/pedido-bot/modelo', payload: Buffer.from('x'),
    headers: { 'content-type': 'application/octet-stream' },
  })
  assert.equal(res.statusCode, 422)
  assert.deepEqual(res.json(), corpo)
})

test('POST /modelo repassa 413', async () => {
  const corpo = { erro: 'modelo_grande', mensagem: 'Arquivo grande demais.' }
  comportamento = { status: 413, json: corpo }
  const res = await app.inject({
    method: 'POST', url: '/api/pedido-bot/modelo', payload: Buffer.from('x'),
    headers: { 'content-type': 'application/octet-stream' },
  })
  assert.equal(res.statusCode, 413)
  assert.deepEqual(res.json(), corpo)
})

test('GET /modelo/info devolve o JSON do robô', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/pedido-bot/modelo/info' })
  assert.equal(res.statusCode, 200)
  assert.equal(res.json().versao, 2)
})

test('robô fora do ar responde 503 no formato { error }', async () => {
  const anterior = process.env.PEDIDO_BOT_URL
  process.env.PEDIDO_BOT_URL = 'http://127.0.0.1:1' // porta fechada
  try {
    const res = await app.inject({ method: 'GET', url: '/api/pedido-bot/modelo/info' })
    assert.equal(res.statusCode, 503)
    assert.deepEqual(res.json(), { error: MSG_INDISPONIVEL })
  } finally {
    process.env.PEDIDO_BOT_URL = anterior
  }
})

test('timeout do robô responde 503', async () => {
  comportamento = { demora: 600 }
  process.env.PEDIDO_BOT_TIMEOUT_MS = '100'
  try {
    const res = await app.inject({
      method: 'POST', url: '/api/pedido-bot/mensagem',
      payload: { conversaId: 'c', texto: 't' },
    })
    assert.equal(res.statusCode, 503)
    assert.deepEqual(res.json(), { error: MSG_INDISPONIVEL })
  } finally {
    process.env.PEDIDO_BOT_TIMEOUT_MS = '90000'
  }
})
