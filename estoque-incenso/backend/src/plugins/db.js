'use strict'

const fp = require('fastify-plugin')
const { Pool } = require('pg')

async function dbPlugin(fastify) {
  const ssl = process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false

  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl,
  })

  pool.on('error', (err) => {
    fastify.log.error({ err }, 'Erro inesperado no pool de conexão com o banco')
  })

  try {
    await pool.query('SELECT 1')
    fastify.log.info('Conexão com o banco de dados estabelecida')
  } catch (err) {
    fastify.log.error({ err, DATABASE_URL: process.env.DATABASE_URL?.replace(/:\/\/.*@/, '://***@') }, 'Falha ao conectar com o banco de dados')
    throw err
  }

  fastify.decorate('db', pool)

  fastify.addHook('onClose', async () => {
    await pool.end()
  })
}

module.exports = fp(dbPlugin, { name: 'db' })
