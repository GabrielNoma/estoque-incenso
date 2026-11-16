'use strict'

const { buscarProducaoDoMes } = require('../queries/producaoMensal')

function rowToRegistro(r) {
  return {
    id: r.id,
    data: r.data_iso,
    quantidade: r.quantidade,
    falta: r.falta,
    motivoFalta: r.motivo_falta,
    observacaoFalta: r.observacao_falta,
  }
}

async function registrosRoutes(fastify) {
  // GET /api/registros?ano=&mes=
  fastify.get('/registros', async (request, reply) => {
    const ano = parseInt(request.query.ano, 10)
    const mes = parseInt(request.query.mes, 10)
    if (!ano || !mes || mes < 1 || mes > 12) {
      return reply.code(400).send({ error: 'Parâmetros "ano" e "mes" são obrigatórios; "mes" deve estar entre 1 e 12.' })
    }

    const funcionarias = await buscarProducaoDoMes(fastify.db, ano, mes)
    return {
      ano,
      mes,
      funcionarias: funcionarias.map(f => ({ ...f, registros: f.registros.map(rowToRegistro) })),
    }
  })

  // PUT /api/registros
  fastify.put('/registros', async (request, reply) => {
    const { funcionariaId, data, quantidade, falta, motivoFalta, observacaoFalta } = request.body || {}

    if (quantidade != null && falta === true) {
      return reply.code(400).send({ error: 'Quantidade e falta não podem ser informados simultaneamente.' })
    }
    if (falta === true && !motivoFalta) {
      return reply.code(400).send({ error: 'Motivo de falta é obrigatório.' })
    }
    if (motivoFalta === 'outro' && !observacaoFalta) {
      return reply.code(400).send({ error: "Observação é obrigatória para motivo 'Outro'." })
    }
    if (quantidade != null && quantidade < 0) {
      return reply.code(400).send({ error: 'Quantidade deve ser maior ou igual a zero.' })
    }

    const func = await fastify.db.query('SELECT id FROM funcionarias WHERE id = $1', [funcionariaId])
    if (func.rowCount === 0) {
      return reply.code(404).send({ error: 'Funcionária não encontrada.' })
    }

    const result = await fastify.db.query(`
      INSERT INTO registros_diarios (funcionaria_id, data, quantidade, falta, motivo_falta, observacao_falta)
      VALUES ($1, $2, $3, $4, $5, $6)
      ON CONFLICT (funcionaria_id, data) DO UPDATE SET
        quantidade       = EXCLUDED.quantidade,
        falta            = EXCLUDED.falta,
        motivo_falta     = EXCLUDED.motivo_falta,
        observacao_falta = EXCLUDED.observacao_falta
      RETURNING id, funcionaria_id, TO_CHAR(data, 'YYYY-MM-DD') AS data_iso, quantidade, falta, motivo_falta, observacao_falta
    `, [funcionariaId, data, quantidade ?? null, falta ?? false, motivoFalta ?? null, observacaoFalta ?? null])

    const r = result.rows[0]
    return {
      id: r.id,
      funcionariaId: r.funcionaria_id,
      data: r.data_iso,
      quantidade: r.quantidade,
      falta: r.falta,
      motivoFalta: r.motivo_falta,
      observacaoFalta: r.observacao_falta,
    }
  })

  // DELETE /api/registros/:id
  fastify.delete('/registros/:id', async (request, reply) => {
    const result = await fastify.db.query('DELETE FROM registros_diarios WHERE id = $1', [request.params.id])
    if (result.rowCount === 0) {
      return reply.code(404).send({ error: 'Registro não encontrado.' })
    }
    return reply.code(204).send()
  })
}

module.exports = registrosRoutes
