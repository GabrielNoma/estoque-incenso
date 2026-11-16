'use strict'

// Fonte única de "quem entra no mês": grade, Resumo Mensal e Excel usam esta função.
// Entra se estiver ativa OU se tiver ao menos um registro no mês (inativa com produção continua contada).
async function buscarProducaoDoMes(db, ano, mes) {
  const result = await db.query(`
    SELECT
      f.id AS funcionaria_id, f.nome, f.ativa,
      r.id, TO_CHAR(r.data, 'YYYY-MM-DD') AS data_iso, EXTRACT(DAY FROM r.data)::int AS dia,
      r.quantidade, r.falta, r.motivo_falta, r.observacao_falta
    FROM funcionarias f
    LEFT JOIN registros_diarios r
      ON r.funcionaria_id = f.id
      AND r.data >= make_date($1::int, $2::int, 1)
      AND r.data <  make_date($1::int, $2::int, 1) + INTERVAL '1 month'
    WHERE f.ativa = true OR r.id IS NOT NULL
    ORDER BY f.nome, r.data
  `, [ano, mes])

  const porFuncionaria = new Map()
  for (const row of result.rows) {
    if (!porFuncionaria.has(row.funcionaria_id)) {
      porFuncionaria.set(row.funcionaria_id, { id: row.funcionaria_id, nome: row.nome, ativa: row.ativa, registros: [] })
    }
    if (row.id != null) porFuncionaria.get(row.funcionaria_id).registros.push(row)
  }
  return Array.from(porFuncionaria.values())
}

module.exports = { buscarProducaoDoMes }
