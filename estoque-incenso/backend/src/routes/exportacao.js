'use strict'

const ExcelJS = require('exceljs')

const COR_FALTA      = 'FFFFFF00'
const COR_FIM_SEMANA = 'FFD3D3D3'
const COR_SEMANA_ISO = 'FFBDD7EE'
const COR_TOTAL      = 'FFC0C0C0'

function diasNoMes(ano, mes) {
  return new Date(ano, mes, 0).getDate()
}

function diaSemana(ano, mes, dia) {
  return new Date(ano, mes - 1, dia).getDay()
}

function semanaISO(ano, mes, dia) {
  const d = new Date(ano, mes - 1, dia)
  const dow = d.getDay() || 7
  d.setDate(d.getDate() + 4 - dow)
  const yearStart = new Date(d.getFullYear(), 0, 1)
  return Math.ceil(((d - yearStart) / 86400000 + 1) / 7)
}

function fill(argb) {
  return { type: 'pattern', pattern: 'solid', fgColor: { argb } }
}

async function exportacaoRoutes(fastify) {
  fastify.get('/exportacao/excel', async (request, reply) => {
    const ano = parseInt(request.query.ano, 10)
    const mes = parseInt(request.query.mes, 10)
    if (!ano || !mes || isNaN(ano) || isNaN(mes) || mes < 1 || mes > 12) {
      return reply.code(400).send({ error: 'Ano e mês são obrigatórios e devem ser válidos.' })
    }

    const result = await fastify.db.query(`
      SELECT
        f.id AS funcionaria_id, f.nome,
        r.id,
        EXTRACT(DAY FROM r.data)::int AS dia,
        r.quantidade, r.falta, r.motivo_falta, r.observacao_falta,
        TO_CHAR(r.data, 'YYYY-MM-DD') AS data_iso
      FROM funcionarias f
      LEFT JOIN registros_diarios r
        ON r.funcionaria_id = f.id
        AND EXTRACT(YEAR FROM r.data) = $1
        AND EXTRACT(MONTH FROM r.data) = $2
      WHERE f.ativa = true OR r.id IS NOT NULL
      ORDER BY f.nome, r.data
    `, [ano, mes])

    const map = new Map()
    for (const row of result.rows) {
      if (!map.has(row.funcionaria_id)) {
        map.set(row.funcionaria_id, { id: row.funcionaria_id, nome: row.nome, registros: {} })
      }
      if (row.id != null) {
        map.get(row.funcionaria_id).registros[row.dia] = row
      }
    }
    const funcionarias = Array.from(map.values())
    const totalDias = diasNoMes(ano, mes)

    // Colunas: dias + totais semanais ISO intercalados após o último dia de cada semana
    const colunas = []
    const semanasVistas = new Set()
    for (let dia = 1; dia <= totalDias; dia++) {
      const sem = semanaISO(ano, mes, dia)
      const dow = diaSemana(ano, mes, dia)
      colunas.push({ tipo: 'dia', dia, dow, sem })
      if (dow === 0 || dia === totalDias) {
        if (!semanasVistas.has(sem)) {
          semanasVistas.add(sem)
          colunas.push({ tipo: 'semana', sem })
        }
      }
    }

    const workbook = new ExcelJS.Workbook()

    // ── Aba Produção ──────────────────────────────────────────────────────────
    const wsProd = workbook.addWorksheet('Produção')

    const header = ['Funcionária']
    for (const col of colunas) {
      header.push(col.tipo === 'dia' ? col.dia : `Sem ${col.sem}`)
    }
    header.push('Total')
    const hRow = wsProd.addRow(header)
    hRow.font = { bold: true }
    for (let ci = 0; ci < colunas.length; ci++) {
      const col = colunas[ci]
      const cell = hRow.getCell(ci + 2)
      if (col.tipo === 'semana') cell.fill = fill(COR_SEMANA_ISO)
      else if (col.dow === 0 || col.dow === 6) cell.fill = fill(COR_FIM_SEMANA)
    }

    const totaisDia = new Array(colunas.length).fill(0)

    for (const func of funcionarias) {
      const rowData = [func.nome]
      let totalFunc = 0
      for (let ci = 0; ci < colunas.length; ci++) {
        const col = colunas[ci]
        if (col.tipo === 'semana') {
          const semTotal = colunas
            .filter(c => c.tipo === 'dia' && c.sem === col.sem)
            .reduce((s, c) => {
              const reg = func.registros[c.dia]
              return s + (reg && !reg.falta && reg.quantidade != null ? reg.quantidade : 0)
            }, 0)
          rowData.push(semTotal)
        } else {
          const reg = func.registros[col.dia]
          if (reg?.falta) {
            rowData.push('FALTA')
          } else if (reg?.quantidade != null) {
            rowData.push(reg.quantidade)
            totalFunc += reg.quantidade
            totaisDia[ci] += reg.quantidade
          } else {
            rowData.push(null)
          }
        }
      }
      rowData.push(totalFunc)
      const dataRow = wsProd.addRow(rowData)
      for (let ci = 0; ci < colunas.length; ci++) {
        const col = colunas[ci]
        const cell = dataRow.getCell(ci + 2)
        if (col.tipo === 'semana') { cell.fill = fill(COR_SEMANA_ISO); cell.font = { bold: true } }
        else if (col.dow === 0 || col.dow === 6) cell.fill = fill(COR_FIM_SEMANA)
        else if (func.registros[col.dia]?.falta) cell.fill = fill(COR_FALTA)
      }
    }

    const totalRow = ['TOTAL DIA']
    let totalGeral = 0
    for (let ci = 0; ci < colunas.length; ci++) {
      if (colunas[ci].tipo === 'semana') { totalRow.push(null); continue }
      totalRow.push(totaisDia[ci] || null)
      totalGeral += totaisDia[ci] || 0
    }
    totalRow.push(totalGeral)
    const tRow = wsProd.addRow(totalRow)
    tRow.font = { bold: true }
    tRow.eachCell(cell => { cell.fill = fill(COR_TOTAL) })

    // ── Aba Faltas ────────────────────────────────────────────────────────────
    const wsFaltas = workbook.addWorksheet('Faltas')
    wsFaltas.addRow(['Funcionária', 'Data', 'Motivo', 'Observação']).font = { bold: true }
    for (const func of funcionarias) {
      for (let dia = 1; dia <= totalDias; dia++) {
        const reg = func.registros[dia]
        if (reg?.falta) {
          wsFaltas.addRow([func.nome, reg.data_iso, reg.motivo_falta ?? '', reg.observacao_falta ?? ''])
        }
      }
    }

    const buffer = await workbook.xlsx.writeBuffer()
    const filename = `producao_${ano}_${String(mes).padStart(2, '0')}.xlsx`
    reply
      .header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
      .header('Content-Disposition', `attachment; filename="${filename}"`)
      .send(Buffer.from(buffer))
  })
}

module.exports = exportacaoRoutes
