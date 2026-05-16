'use strict'

const { test, before, after } = require('node:test')
const assert = require('node:assert/strict')
const { buildTestApp } = require('./helpers')

let app
let funcId
let registroId

before(async () => {
  app = await buildTestApp()
  await app.db.query("DELETE FROM registros_diarios WHERE funcionaria_id IN (SELECT id FROM funcionarias WHERE nome = 'TESTR_reg')")
  await app.db.query("DELETE FROM funcionarias WHERE nome = 'TESTR_reg'")
  const r = await app.db.query("INSERT INTO funcionarias (nome) VALUES ('TESTR_reg') RETURNING id")
  funcId = r.rows[0].id
})

after(async () => {
  await app.db.query('DELETE FROM registros_diarios WHERE funcionaria_id = $1', [funcId])
  await app.db.query('DELETE FROM funcionarias WHERE id = $1', [funcId])
  await app.close()
})

// ── GET /api/registros ───────────────────────────────────────────────────────

test('GET /api/registros — retorna estrutura correta [GREEN]', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/registros?ano=2026&mes=5' })
  assert.equal(res.statusCode, 200)
  const body = JSON.parse(res.body)
  assert.ok('ano' in body && 'mes' in body && Array.isArray(body.funcionarias))
})

test('GET /api/registros — sem params retorna 400 [RED]', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/registros' })
  assert.equal(res.statusCode, 400)
})

test('GET /api/registros — mes inválido retorna 400 [RED]', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/registros?ano=2026&mes=abc' })
  assert.equal(res.statusCode, 400)
})

// ── PUT /api/registros ───────────────────────────────────────────────────────

test('PUT /api/registros — salva produção [GREEN]', async () => {
  const res = await app.inject({
    method: 'PUT', url: '/api/registros',
    payload: { funcionariaId: funcId, data: '2026-05-10', quantidade: 50, falta: false, motivoFalta: null, observacaoFalta: null }
  })
  assert.equal(res.statusCode, 200)
  const body = JSON.parse(res.body)
  assert.equal(body.quantidade, 50)
  assert.equal(body.falta, false)
  assert.equal(body.data, '2026-05-10')
  registroId = body.id
})

test('PUT /api/registros — upsert atualiza registro existente [GREEN]', async () => {
  const res = await app.inject({
    method: 'PUT', url: '/api/registros',
    payload: { funcionariaId: funcId, data: '2026-05-10', quantidade: 80, falta: false, motivoFalta: null, observacaoFalta: null }
  })
  assert.equal(res.statusCode, 200)
  assert.equal(JSON.parse(res.body).quantidade, 80)
})

test('PUT /api/registros — salva falta com motivo [GREEN]', async () => {
  const res = await app.inject({
    method: 'PUT', url: '/api/registros',
    payload: { funcionariaId: funcId, data: '2026-05-11', quantidade: null, falta: true, motivoFalta: 'atestado', observacaoFalta: null }
  })
  assert.equal(res.statusCode, 200)
  const body = JSON.parse(res.body)
  assert.equal(body.falta, true)
  assert.equal(body.motivoFalta, 'atestado')
})

test('PUT /api/registros — falta com motivo outro e observação [GREEN]', async () => {
  const res = await app.inject({
    method: 'PUT', url: '/api/registros',
    payload: { funcionariaId: funcId, data: '2026-05-12', quantidade: null, falta: true, motivoFalta: 'outro', observacaoFalta: 'Viagem' }
  })
  assert.equal(res.statusCode, 200)
  assert.equal(JSON.parse(res.body).observacaoFalta, 'Viagem')
})

test('PUT /api/registros — quantidade + falta simultâneos retorna 400 [RED]', async () => {
  const res = await app.inject({
    method: 'PUT', url: '/api/registros',
    payload: { funcionariaId: funcId, data: '2026-05-13', quantidade: 10, falta: true, motivoFalta: 'falta', observacaoFalta: null }
  })
  assert.equal(res.statusCode, 400)
  assert.equal(JSON.parse(res.body).error, 'Quantidade e falta não podem ser informados simultaneamente.')
})

test('PUT /api/registros — falta sem motivo retorna 400 [RED]', async () => {
  const res = await app.inject({
    method: 'PUT', url: '/api/registros',
    payload: { funcionariaId: funcId, data: '2026-05-14', quantidade: null, falta: true, motivoFalta: null, observacaoFalta: null }
  })
  assert.equal(res.statusCode, 400)
  assert.equal(JSON.parse(res.body).error, 'Motivo de falta é obrigatório.')
})

test('PUT /api/registros — motivo outro sem observação retorna 400 [RED]', async () => {
  const res = await app.inject({
    method: 'PUT', url: '/api/registros',
    payload: { funcionariaId: funcId, data: '2026-05-15', quantidade: null, falta: true, motivoFalta: 'outro', observacaoFalta: null }
  })
  assert.equal(res.statusCode, 400)
  assert.match(JSON.parse(res.body).error, /Observação/)
})

test('PUT /api/registros — quantidade negativa retorna 400 [RED]', async () => {
  const res = await app.inject({
    method: 'PUT', url: '/api/registros',
    payload: { funcionariaId: funcId, data: '2026-05-16', quantidade: -5, falta: false, motivoFalta: null, observacaoFalta: null }
  })
  assert.equal(res.statusCode, 400)
})

test('PUT /api/registros — funcionária inexistente retorna 404 [RED]', async () => {
  const res = await app.inject({
    method: 'PUT', url: '/api/registros',
    payload: { funcionariaId: 999999, data: '2026-05-17', quantidade: 10, falta: false, motivoFalta: null, observacaoFalta: null }
  })
  assert.equal(res.statusCode, 404)
})

// ── DELETE /api/registros/:id ────────────────────────────────────────────────

test('DELETE /api/registros/:id — remove registro [GREEN]', async () => {
  const res = await app.inject({ method: 'DELETE', url: `/api/registros/${registroId}` })
  assert.equal(res.statusCode, 204)
})

test('DELETE /api/registros/:id — id inexistente retorna 404 [RED]', async () => {
  const res = await app.inject({ method: 'DELETE', url: '/api/registros/999999' })
  assert.equal(res.statusCode, 404)
})
