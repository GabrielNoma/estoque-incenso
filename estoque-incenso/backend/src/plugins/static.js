'use strict'

const fp = require('fastify-plugin')
const fastifyStatic = require('@fastify/static')
const path = require('path')
const fs = require('fs')

const distPath = path.join(__dirname, '../../../frontend/dist/frontend/browser')

async function staticPlugin(fastify) {
  if (!fs.existsSync(distPath)) {
    fastify.log.warn('frontend/dist/browser não encontrado — static serving desabilitado. Execute "npm run build" no frontend para habilitar.')
    return
  }

  await fastify.register(fastifyStatic, {
    root: distPath,
    prefix: '/',
    wildcard: false,
  })

  fastify.addHook('onRequest', async (request, reply) => {
    if (!request.url.startsWith('/api')) {
      try {
        return reply.sendFile('index.html')
      } catch {
        // arquivo estático não encontrado — Fastify trata normalmente
      }
    }
  })
}

module.exports = fp(staticPlugin, { name: 'static' })
