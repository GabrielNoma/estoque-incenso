'use strict'

const fp = require('fastify-plugin')
const fastifyStatic = require('@fastify/static')
const path = require('path')
const fs = require('fs')

const distPath = path.join(__dirname, '../../../frontend/dist/frontend/browser')

async function staticPlugin(fastify) {
  if (!fs.existsSync(distPath)) {
    fastify.log.warn('frontend/dist/frontend/browser não encontrado — static serving desabilitado. Execute "npm run build" no frontend para habilitar.')
    return
  }

  await fastify.register(fastifyStatic, {
    root: distPath,
    prefix: '/',
  })

  // SPA fallback: URLs sem extensão (rotas Angular) → index.html
  // URLs com extensão que não existem (assets) → 404 normal
  fastify.setNotFoundHandler((request, reply) => {
    if (request.url.startsWith('/api') || path.extname(request.url.split('?')[0])) {
      return reply.code(404).send({ error: 'Not found' })
    }
    return reply.sendFile('index.html')
  })
}

module.exports = fp(staticPlugin, { name: 'static' })
