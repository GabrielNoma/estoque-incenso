'use strict'

const { test, before, after } = require('node:test')
const assert = require('node:assert/strict')
const ExcelJS = require('exceljs')
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

test('GET /api/exportacao/excel — última linha da aba Produção tem rótulo TOTAL MENSAL [GREEN]', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/exportacao/excel?ano=2026&mes=5' })
  assert.equal(res.statusCode, 200)
  const workbook = new ExcelJS.Workbook()
  await workbook.xlsx.load(res.rawPayload)
  const ws = workbook.getWorksheet('Produção')
  assert.ok(ws, 'aba Produção deve existir')
  const lastRow = ws.getRow(ws.rowCount)
  const primeiraCell = lastRow.getCell(1).value
  assert.equal(primeiraCell, 'TOTAL MENSAL', 'última linha deve ter rótulo TOTAL MENSAL')
})

test('GET /api/exportacao/excel — não existe célula com texto TOTAL DIA [RED]', async () => {
  const res = await app.inject({ method: 'GET', url: '/api/exportacao/excel?ano=2026&mes=5' })
  assert.equal(res.statusCode, 200)
  const workbook = new ExcelJS.Workbook()
  await workbook.xlsx.load(res.rawPayload)
  const ws = workbook.getWorksheet('Produção')
  assert.ok(ws, 'aba Produção deve existir')
  let encontrou = false
  ws.eachRow(row => {
    row.eachCell(cell => {
      if (cell.value === 'TOTAL DIA') encontrou = true
    })
  })
  assert.equal(encontrou, false, 'não deve existir célula com texto TOTAL DIA')
})

test('GET /api/exportacao/excel — total mensal é igual à soma das quantidades válidas [GREEN]', async () => {
  const { rows } = await app.db.query(`
    SELECT COALESCE(SUM(r.quantidade), 0)::int AS total
    FROM registros_diarios r
    JOIN funcionarias f ON f.id = r.funcionaria_id
    WHERE EXTRACT(YEAR FROM r.data) = 2026
      AND EXTRACT(MONTH FROM r.data) = 5
      AND r.falta = false
      AND r.quantidade IS NOT NULL
  `)
  const expectedTotal = rows[0].total

  const res = await app.inject({ method: 'GET', url: '/api/exportacao/excel?ano=2026&mes=5' })
  assert.equal(res.statusCode, 200)
  const workbook = new ExcelJS.Workbook()
  await workbook.xlsx.load(res.rawPayload)
  const ws = workbook.getWorksheet('Produção')
  assert.ok(ws, 'aba Produção deve existir')
  const lastRow = ws.getRow(ws.rowCount)
  let totalMensal = null
  lastRow.eachCell({ includeEmpty: false }, cell => {
    if (typeof cell.value === 'number') totalMensal = cell.value
  })
  assert.equal(totalMensal, expectedTotal, `total mensal no Excel deve bater com a soma do banco (${expectedTotal})`)
})
