'use strict'

const { test, before, after } = require('node:test')
const assert = require('node:assert/strict')
const { buildTestApp } = require('./helpers')

let app
let idCriado

// Prefixo único para evitar conflito com outros arquivos de teste rodando em paralelo
const PREFIX = 'TESTEF_'

async function limpar(db) {
  await db.query(`DELETE FROM registros_diarios WHERE funcionaria_id IN (SELECT id FROM funcionarias WHERE nome LIKE '${PREFIX}%')`)
  await db.query(`DELETE FROM funcionarias WHERE nome LIKE '${PREFIX}%'`)
}

before(async () => {
  app = await buildTestApp()
  await limpar(app.db)
})

after(async () => {
  await limpar(app.db)
  await app.close()
})

// ── GET /api/funcionarias ────────────────────────────────────────────────────

test('GET /api/funcionarias — retorna array', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/funcionarias' })
  assert.equal(res.statusCode, 200)
  assert.ok(Array.isArray(JSON.parse(res.body)))
})

test('GET /api/funcionarias — retorna apenas ativas por padrão', async () => {
  await app.db.query("INSERT INTO funcionarias (nome, ativa) VALUES ('TESTEF_inativa', false)")
  const res = await app.inject({ method: 'GET', url: '/api/funcionarias' })
  const body = JSON.parse(res.body)
  assert.ok(!body.some(f => f.nome === 'TESTEF_inativa'))
})

test('GET /api/funcionarias?includeInactive=true — inclui inativas', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/funcionarias?includeInactive=true' })
  const body = JSON.parse(res.body)
  assert.ok(body.some(f => f.nome === 'TESTEF_inativa'))
})

// ── POST /api/funcionarias ───────────────────────────────────────────────────

test('POST /api/funcionarias — cria funcionária [GREEN]', async () => {
  const res = await app.inject({
    method: 'POST', url: '/api/funcionarias',
    payload: { nome: 'TESTEF_nova' }
  })
  assert.equal(res.statusCode, 201)
  const body = JSON.parse(res.body)
  assert.ok(body.id)
  assert.equal(body.nome, 'TESTEF_nova')
  assert.equal(body.ativa, true)
  idCriado = body.id
})

test('POST /api/funcionarias — nome duplicado retorna 409 [RED]', async () => {
  const res = await app.inject({
    method: 'POST', url: '/api/funcionarias',
    payload: { nome: 'TESTEF_nova' }
  })
  assert.equal(res.statusCode, 409)
  assert.equal(JSON.parse(res.body).error, 'Funcionária com este nome já existe.')
})

test('POST /api/funcionarias — nome vazio retorna 400 [RED]', async () => {
  const res = await app.inject({
    method: 'POST', url: '/api/funcionarias',
    payload: { nome: '' }
  })
  assert.equal(res.statusCode, 400)
})

test('POST /api/funcionarias — sem body retorna 400 [RED]', async () => {
  const res = await app.inject({ method: 'POST', url: '/api/funcionarias', payload: {} })
  assert.equal(res.statusCode, 400)
})

// ── PUT /api/funcionarias/:id ────────────────────────────────────────────────

test('PUT /api/funcionarias/:id — atualiza nome [GREEN]', async () => {
  const res = await app.inject({
    method: 'PUT', url: `/api/funcionarias/${idCriado}`,
    payload: { nome: 'TESTEF_atualizada' }
  })
  assert.equal(res.statusCode, 200)
  assert.equal(JSON.parse(res.body).nome, 'TESTEF_atualizada')
})

test('PUT /api/funcionarias/:id — id inexistente retorna 404 [RED]', async () => {
  const res = await app.inject({
    method: 'PUT', url: '/api/funcionarias/999999',
    payload: { nome: 'TESTEF_x' }
  })
  assert.equal(res.statusCode, 404)
})

test('PUT /api/funcionarias/:id — nome vazio retorna 400 [RED]', async () => {
  const res = await app.inject({
    method: 'PUT', url: `/api/funcionarias/${idCriado}`,
    payload: { nome: '' }
  })
  assert.equal(res.statusCode, 400)
})

// ── PATCH /api/funcionarias/:id/status ──────────────────────────────────────

test('PATCH /api/funcionarias/:id/status — desativa [GREEN]', async () => {
  const res = await app.inject({
    method: 'PATCH', url: `/api/funcionarias/${idCriado}/status`,
    payload: { ativa: false }
  })
  assert.equal(res.statusCode, 200)
  assert.equal(JSON.parse(res.body).ativa, false)
})

test('PATCH /api/funcionarias/:id/status — ativa novamente [GREEN]', async () => {
  const res = await app.inject({
    method: 'PATCH', url: `/api/funcionarias/${idCriado}/status`,
    payload: { ativa: true }
  })
  assert.equal(res.statusCode, 200)
  assert.equal(JSON.parse(res.body).ativa, true)
})

test('PATCH /api/funcionarias/:id/status — id inexistente retorna 404 [RED]', async () => {
  const res = await app.inject({
    method: 'PATCH', url: '/api/funcionarias/999999/status',
    payload: { ativa: false }
  })
  assert.equal(res.statusCode, 404)
})

test('PATCH /api/funcionarias/:id/status — campo ativa não-boolean retorna 400 [RED]', async () => {
  const res = await app.inject({
    method: 'PATCH', url: `/api/funcionarias/${idCriado}/status`,
    payload: { ativa: 'sim' }
  })
  assert.equal(res.statusCode, 400)
})
