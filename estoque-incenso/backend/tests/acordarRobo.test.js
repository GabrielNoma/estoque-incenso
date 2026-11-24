'use strict'

// Plano gratuito do Render: o robô dorme e leva ~80 s para acordar. Quando alguém abre uma PÁGINA do
// estoque, o servidor avisa o robô (GET /saude, sem esperar) para ele já estar de pé quando a pessoa
// escolher o menu. No máximo um aviso por intervalo, para recarregar a página não gerar chamadas à toa.

const { test, before, after } = require('node:test')
const assert = require('node:assert/strict')
const http = require('node:http')
const { buildTestApp } = require('./helpers')

let bot
let saudes // quantas vezes o robô falso recebeu GET /saude
let outras // outras requisições que NÃO deveriam chegar

before(async () => {
  bot = http.createServer((req, res) => {
    if (req.url === '/saude') saudes += 1
    else outras += 1
    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end('{"status":"ok"}')
  })
  await new Promise((r) => bot.listen(0, '127.0.0.1', r))
  process.env.PEDIDO_BOT_URL = `http://127.0.0.1:${bot.address().port}`
})

after(async () => { await new Promise((r) => bot.close(r)) })

test.beforeEach(() => { saudes = 0; outras = 0; delete process.env.PEDIDO_BOT_ACORDAR_INTERVALO_MS })

const esperar = (ms) => new Promise((r) => setTimeout(r, ms))
async function esperarSaudes(n) {
  for (let i = 0; i < 40 && saudes < n; i++) await esperar(25)
}

test('abrir uma página avisa o robô uma vez, sem chave e sem esperar a resposta', async () => {
  const app = await buildTestApp()
  try {
    await app.inject({ method: 'GET', url: '/' })
    await esperarSaudes(1)
    assert.equal(saudes, 1)
    assert.equal(outras, 0)
  } finally { await app.close() }
})

test('várias páginas dentro do intervalo avisam o robô uma única vez', async () => {
  const app = await buildTestApp()
  try {
    for (const url of ['/', '/pedidos', '/historico-pedidos-bot?x=1', '/']) {
      await app.inject({ method: 'GET', url })
    }
    await esperarSaudes(1)
    await esperar(150)
    assert.equal(saudes, 1)
  } finally { await app.close() }
})

test('passado o intervalo, avisa de novo', async () => {
  process.env.PEDIDO_BOT_ACORDAR_INTERVALO_MS = '0'
  const app = await buildTestApp()
  try {
    await app.inject({ method: 'GET', url: '/' })
    await app.inject({ method: 'GET', url: '/pedidos' })
    await esperarSaudes(2)
    assert.equal(saudes, 2)
  } finally { await app.close() }
})

test('API, arquivos e métodos que não são GET não avisam o robô', async () => {
  const app = await buildTestApp()
  try {
    await app.inject({ method: 'GET', url: '/api/funcionarias' })
    await app.inject({ method: 'GET', url: '/main-ABC123.js' })
    await app.inject({ method: 'GET', url: '/favicon.ico' })
    await app.inject({ method: 'POST', url: '/pedidos' })
    await esperar(200)
    assert.equal(saudes, 0)
  } finally { await app.close() }
})

test('robô fora do ar não atrapalha a página', async () => {
  const antes = process.env.PEDIDO_BOT_URL
  process.env.PEDIDO_BOT_URL = 'http://127.0.0.1:1' // porta fechada
  const app = await buildTestApp()
  try {
    const res = await app.inject({ method: 'GET', url: '/' })
    assert.ok(res.statusCode < 500, `status ${res.statusCode}`)
    await esperar(200) // dá tempo da falha acontecer sem derrubar o processo
  } finally {
    process.env.PEDIDO_BOT_URL = antes
    await app.close()
  }
})
