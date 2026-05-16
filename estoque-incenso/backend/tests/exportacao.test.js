'use strict'

const { test, before, after } = require('node:test')
const assert = require('node:assert/strict')
const { buildTestApp } = require('./helpers')

let app
let funcId

before(async () => {
  app = await buildTestApp()
  await app.db.query("DELETE FROM registros_diarios WHERE funcionaria_id IN (SELECT id FROM funcionarias WHERE nome = 'TESTEX_excel')")
  await app.db.query("DELETE FROM funcionarias WHERE nome = 'TESTEX_excel'")
  const r = await app.db.query("INSERT INTO funcionarias (nome) VALUES ('TESTEX_excel') RETURNING id")
  funcId = r.rows[0].id
  await app.db.query(
    'INSERT INTO registros_diarios (funcionaria_id, data, quantidade, falta) VALUES ($1, $2, $3, false)',
    [funcId, '2026-05-01', 45]
  )
  await app.db.query(
    'INSERT INTO registros_diarios (funcionaria_id, data, falta, motivo_falta) VALUES ($1, $2, true, $3)',
    [funcId, '2026-05-02', 'atestado']
  )
})

after(async () => {
  await app.db.query('DELETE FROM registros_diarios WHERE funcionaria_id = $1', [funcId])
  await app.db.query('DELETE FROM funcionarias WHERE id = $1', [funcId])
  await app.close()
})

test('GET /api/exportacao/excel — retorna arquivo xlsx [GREEN]', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/exportacao/excel?ano=2026&mes=5' })
  assert.equal(res.statusCode, 200)
  assert.equal(res.headers['content-type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
  assert.match(res.headers['content-disposition'], /producao_2026_05\.xlsx/)
  assert.ok(res.rawPayload.length > 0, 'body não deve ser vazio')
})

test('GET /api/exportacao/excel — sem params retorna 400 [RED]', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/exportacao/excel' })
  assert.equal(res.statusCode, 400)
  assert.equal(JSON.parse(res.body).error, 'Ano e mês são obrigatórios e devem ser válidos.')
})

test('GET /api/exportacao/excel — mes 0 retorna 400 [RED]', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/exportacao/excel?ano=2026&mes=0' })
  assert.equal(res.statusCode, 400)
})

test('GET /api/exportacao/excel — mes 13 retorna 400 [RED]', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/exportacao/excel?ano=2026&mes=13' })
  assert.equal(res.statusCode, 400)
})

test('GET /api/exportacao/excel — mes texto retorna 400 [RED]', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/exportacao/excel?ano=2026&mes=abc' })
  assert.equal(res.statusCode, 400)
})

test('GET /api/exportacao/excel — mes sem dados gera arquivo vazio válido [GREEN]', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/exportacao/excel?ano=2000&mes=1' })
  assert.equal(res.statusCode, 200)
  assert.match(res.headers['content-disposition'], /producao_2000_01\.xlsx/)
})
