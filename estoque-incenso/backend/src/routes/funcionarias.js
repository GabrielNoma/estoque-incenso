'use strict'

const COLUNAS = `id, nome, ativa, TO_CHAR(inativada_em, 'YYYY-MM-DD') AS "inativadaEm"`

async function funcionariasRoutes(fastify) {
  // GET /api/funcionarias
  fastify.get('/funcionarias', async (request, reply) => {
    const includeInactive = request.query.incluirInativas === 'true'
    const sql = includeInactive
      ? `SELECT ${COLUNAS} FROM funcionarias ORDER BY nome`
      : `SELECT ${COLUNAS} FROM funcionarias WHERE ativa = true ORDER BY nome`
    const result = await fastify.db.query(sql)
    return result.rows
  })

  // POST /api/funcionarias
  fastify.post('/funcionarias', async (request, reply) => {
    const { nome } = request.body || {}
    if (!nome || !nome.trim()) {
      return reply.code(400).send({ error: 'Nome é obrigatório.' })
    }
    try {
      const result = await fastify.db.query(
        `INSERT INTO funcionarias (nome) VALUES ($1) RETURNING ${COLUNAS}`,
        [nome.trim()]
      )
      return reply.code(201).send(result.rows[0])
    } catch (err) {
      if (err.code === '23505') {
        return reply.code(409).send({ error: 'Funcionária com este nome já existe.' })
      }
      throw err
    }
  })

  // PUT /api/funcionarias/:id
  fastify.put('/funcionarias/:id', async (request, reply) => {
    const { id } = request.params
    const { nome } = request.body || {}
    if (!nome || !nome.trim()) {
      return reply.code(400).send({ error: 'Nome é obrigatório.' })
    }
    const result = await fastify.db.query(
      `UPDATE funcionarias SET nome=$1 WHERE id=$2 RETURNING ${COLUNAS}`,
      [nome.trim(), id]
    )
    if (result.rowCount === 0) {
      return reply.code(404).send({ error: 'Funcionária não encontrada.' })
    }
    return result.rows[0]
  })

  // PATCH /api/funcionarias/:id/status
  fastify.patch('/funcionarias/:id/status', async (request, reply) => {
    const { id } = request.params
    const { ativa } = request.body || {}
    if (typeof ativa !== 'boolean') {
      return reply.code(400).send({ error: 'Campo "ativa" deve ser boolean.' })
    }
    const result = await fastify.db.query(
      // Guarda a data de inativação: meses até ela continuam mostrando a funcionária,
      // meses posteriores não. Reativar limpa a data.
      `UPDATE funcionarias
       SET ativa=$1,
           inativada_em = CASE WHEN $1 THEN NULL
                               ELSE COALESCE(inativada_em, (now() AT TIME ZONE 'America/Sao_Paulo')::date) END
       WHERE id=$2 RETURNING ${COLUNAS}`,
      [ativa, id]
    )
    if (result.rowCount === 0) {
      return reply.code(404).send({ error: 'Funcionária não encontrada.' })
    }
    return result.rows[0]
  })
}

module.exports = funcionariasRoutes
