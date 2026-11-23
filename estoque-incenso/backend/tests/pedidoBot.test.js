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
  if (req.method === 'GET' && req.url.startsWith('/api/pedidos?')) {
    return enviarJson(res, 200, {
      pedidos: [
        { id: 12, conversa: '5511999990000', mensagem: '2 dz ogum', itens: [{ nome: 'Ogum', quantidade: 2 }],
          lista: 'Ogum — 2 dz\n\nok ou não?', estado: 'confirmado', resposta: 'ok', criado_em: '2026-11-23T10:00:00+00:00',
          respondido_em: '2026-11-23T10:01:00+00:00', modelo_versao: 1,
          arquivo: { nome: 'pedido-12.xlsx', url: '/api/pedidos/12/planilha' } },
        { id: 11, conversa: '3f2a9c1e-7b1d-4e55-9a10-aaaabbbbcccc', mensagem: 'abre caminho', itens: [{ nome: 'Abre Caminho', quantidade: 1 }],
          lista: 'Abre Caminho — 1 dz\n\nok ou não?', estado: 'recusado', resposta: 'não', criado_em: '2026-11-23T09:00:00+00:00',
          respondido_em: '2026-11-23T09:01:00+00:00', modelo_versao: null, arquivo: null },
      ],
      proximo: 11,
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

// -- chave de acesso do robô (bot em produção exige Authorization em toda rota, menos /saude) -------------------
const CHAVE_TESTE = 'chave-de-teste-do-estoque-com-mais-de-32-caracteres'
const MSG_ACESSO = 'O serviço de pedidos recusou o acesso. Avise o responsável: a chave do robô precisa ser conferida.'
const MSG_MUITAS = 'Muitas mensagens seguidas. Aguarde um instante e tente de novo.'

const ROTAS = [
  { metodo: 'POST', url: '/api/pedido-bot/mensagem', payload: { conversaId: 'c', texto: 'ogum' } },
  { metodo: 'GET', url: '/api/pedido-bot/planilha/12' },
  { metodo: 'GET', url: '/api/pedido-bot/modelo' },
  { metodo: 'GET', url: '/api/pedido-bot/modelo/info' },
  { metodo: 'GET', url: '/api/pedido-bot/historico' },
  { metodo: 'POST', url: '/api/pedido-bot/modelo', payload: Buffer.from('xlsx'),
    headers: { 'content-type': 'application/octet-stream' } },
]

function injetar(rota) {
  return app.inject({ method: rota.metodo, url: rota.url, payload: rota.payload, headers: rota.headers })
}

test('com PEDIDO_BOT_API_KEY, toda chamada ao robô leva Authorization: Bearer; a chave nunca volta ao navegador', async () => {
  process.env.PEDIDO_BOT_API_KEY = CHAVE_TESTE
  try {
    for (const rota of ROTAS) {
      recebido = null
      const res = await injetar(rota)
      assert.equal(recebido.headers.authorization, `Bearer ${CHAVE_TESTE}`, rota.url)
      assert.ok(!res.payload.includes(CHAVE_TESTE) && !JSON.stringify(res.headers).includes(CHAVE_TESTE), rota.url)
    }
  } finally { delete process.env.PEDIDO_BOT_API_KEY }
})

test('sem PEDIDO_BOT_API_KEY, nenhum cabeçalho Authorization é enviado (uso local)', async () => {
  delete process.env.PEDIDO_BOT_API_KEY
  await injetar(ROTAS[2])
  assert.equal(recebido.headers.authorization, undefined)
})

test('401 e 403 do robô viram 502 com aviso em português, em todas as rotas, sem vazar o corpo do robô', async () => {
  for (const status of [401, 403]) {
    for (const rota of ROTAS) {
      comportamento = { status, json: { erro: 'chave_invalida', mensagem: 'Chave de acesso inválida.' } }
      const res = await injetar(rota)
      assert.equal(res.statusCode, 502, `${status} ${rota.url}`)
      assert.deepEqual(res.json(), { error: MSG_ACESSO })
    }
  }
})

test('429 do robô vira 429 com aviso em português e sem vazar o corpo do robô', async () => {
  for (const rota of ROTAS) {
    comportamento = { status: 429, json: { erro: 'muitas_requisicoes', mensagem: 'Muitas requisições.' } }
    const res = await injetar(rota)
    assert.equal(res.statusCode, 429, rota.url)
    assert.deepEqual(res.json(), { error: MSG_MUITAS })
  }
})

test('413 e 422 do robô continuam chegando à tela com a mensagem do robô (modelo inválido ou grande)', async () => {
  comportamento = { status: 422, json: { erro: 'modelo_invalido', mensagem: 'Confira o modelo.' } }
  const invalido = await injetar(ROTAS[5])
  assert.equal(invalido.statusCode, 422)
  assert.equal(invalido.json().mensagem, 'Confira o modelo.')
  comportamento = { status: 413, json: { erro: 'modelo_grande', mensagem: 'Arquivo grande demais.' } }
  const grande = await injetar(ROTAS[5])
  assert.equal(grande.statusCode, 413)
  assert.equal(grande.json().mensagem, 'Arquivo grande demais.')
})

test('a resposta de recusa não carrega a chave nem o texto do pedido', async () => {
  process.env.PEDIDO_BOT_API_KEY = CHAVE_TESTE
  try {
    comportamento = { status: 401, json: { erro: 'chave_invalida', mensagem: 'x' } }
    const res = await app.inject({ method: 'POST', url: '/api/pedido-bot/mensagem',
      payload: { conversaId: 'segredo-da-conversa', texto: 'texto-secreto-do-pedido' } })
    assert.equal(res.statusCode, 502)
    assert.ok(!res.payload.includes(CHAVE_TESTE) && !res.payload.includes('texto-secreto-do-pedido'))
  } finally { delete process.env.PEDIDO_BOT_API_KEY }
})

// -- diagnóstico: o log diz POR QUE o robô está indisponível, sem vazar a chave nem o texto ---------------------
const { classificarFalha } = require('../src/routes/pedidoBot')

test('classificarFalha: url sem protocolo, chave com caracteres inválidos, recusa de conexão e tempo esgotado', () => {
  const tipo = new TypeError('fetch failed')
  assert.equal(classificarFalha(new TypeError('x'), { url: 'pedido-bot.onrender.com', chave: 'abc' }), 'url_invalida')
  assert.equal(classificarFalha(new TypeError('x'), { url: 'https://ok.onrender.com', chave: 'abc\ndef' }), 'chave_com_caracteres_invalidos')
  assert.equal(classificarFalha(new TypeError('x'), { url: 'https://ok.onrender.com', chave: 'abc def' }), 'chave_com_caracteres_invalidos')
  assert.equal(classificarFalha(new TypeError('x'), { url: 'https://ok.onrender.com', chave: 'chave••••' }), 'chave_com_caracteres_invalidos')
  const recusada = Object.assign(new TypeError('fetch failed'), { cause: { code: 'ECONNREFUSED' } })
  assert.equal(classificarFalha(recusada, { url: 'http://127.0.0.1:8000', chave: '' }), 'conexao_recusada')
  const semDns = Object.assign(new TypeError('fetch failed'), { cause: { code: 'ENOTFOUND' } })
  assert.equal(classificarFalha(semDns, { url: 'https://nao-existe.exemplo', chave: '' }), 'endereco_nao_encontrado')
  assert.equal(classificarFalha(Object.assign(new Error('x'), { name: 'AbortError' }), { url: 'https://ok.exemplo', chave: '' }), 'tempo_esgotado')
  assert.equal(classificarFalha(tipo, { url: 'https://ok.exemplo', chave: 'abc' }), 'TypeError')
})

test('classificarFalha nunca devolve o valor da chave nem a mensagem do erro', () => {
  const erro = new TypeError('Headers.append: "Bearer SEGREDO" is an invalid header value.')
  const motivo = classificarFalha(erro, { url: 'https://ok.exemplo', chave: 'SEGREDO\n' })
  assert.ok(!motivo.includes('SEGREDO') && !motivo.includes('Headers'))
})

test('com a URL do robô sem protocolo a tela recebe o aviso em português (e o motivo vai só para o log)', async () => {
  const anterior = process.env.PEDIDO_BOT_URL
  process.env.PEDIDO_BOT_URL = 'pedido-bot.onrender.com'
  try {
    const res = await app.inject({ method: 'GET', url: '/api/pedido-bot/modelo/info' })
    assert.equal(res.statusCode, 503)
    assert.deepEqual(res.json(), { error: MSG_INDISPONIVEL })
  } finally { process.env.PEDIDO_BOT_URL = anterior }
})


// -- histórico de pedidos do robô ------------------------------------------------------------------------------
test('GET /historico encaminha os filtros, mascara a conversa e reescreve a url da planilha', async () => {
  process.env.PEDIDO_BOT_API_KEY = CHAVE_TESTE
  try {
    const res = await app.inject({ method: 'GET', url: '/api/pedido-bot/historico?limite=20&antes=30&estado=confirmado' })
    assert.equal(res.statusCode, 200)
    assert.equal(recebido.url, '/api/pedidos?limite=20&antes=30&estado=confirmado')
    assert.equal(recebido.headers.authorization, `Bearer ${CHAVE_TESTE}`)
    const corpo = res.json()
    assert.equal(corpo.proximo, 11)
    assert.deepEqual(corpo.pedidos.map((p) => p.id), [12, 11])
    assert.equal(corpo.pedidos[0].conversa, '…0000')
    assert.equal(corpo.pedidos[1].conversa, '…cccc')
    assert.deepEqual(corpo.pedidos[0].arquivo, { nome: 'pedido-12.xlsx', url: '/api/pedido-bot/planilha/12' })
    assert.equal(corpo.pedidos[1].arquivo, null)
    assert.deepEqual(corpo.pedidos[0].itens, [{ nome: 'Ogum', quantidade: 2 }])
    assert.equal(corpo.pedidos[0].estado, 'confirmado')
    assert.ok(!res.payload.includes('5511999990000') && !res.payload.includes('3f2a9c1e'), 'a conversa completa não pode chegar ao navegador')
    assert.ok(!res.payload.includes(CHAVE_TESTE))
  } finally { delete process.env.PEDIDO_BOT_API_KEY }
})

test('GET /historico sem filtros usa os padrões do robô', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/pedido-bot/historico' })
  assert.equal(res.statusCode, 200)
  assert.equal(recebido.url, '/api/pedidos?limite=50')
})

test('GET /historico com filtro inválido responde 400 em português sem chamar o robô', async () => {
  for (const consulta of ['limite=0', 'limite=201', 'limite=abc', 'antes=abc', 'antes=0', 'estado=inventado']) {
    recebido = null
    const res = await app.inject({ method: 'GET', url: `/api/pedido-bot/historico?${consulta}` })
    assert.equal(res.statusCode, 400, consulta)
    assert.deepEqual(res.json(), { error: 'Filtro inválido.' })
    assert.equal(recebido, null, consulta)
  }
})

test('GET /historico: robô fora do ar vira 503 em português', async () => {
  const anterior = process.env.PEDIDO_BOT_URL
  process.env.PEDIDO_BOT_URL = 'http://127.0.0.1:1'
  try {
    const res = await app.inject({ method: 'GET', url: '/api/pedido-bot/historico' })
    assert.equal(res.statusCode, 503)
    assert.deepEqual(res.json(), { error: MSG_INDISPONIVEL })
  } finally { process.env.PEDIDO_BOT_URL = anterior }
})
