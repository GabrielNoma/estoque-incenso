'use strict'

const fp = require('fastify-plugin')
const cors = require('@fastify/cors')

async function corsPlugin(fastify) {
  await fastify.register(cors, { origin: true })
}

module.exports = fp(corsPlugin, { name: 'cors' })
