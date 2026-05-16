'use strict'

const fastify = require('fastify')

function buildApp() {
  const app = fastify({
    logger: {
      level: process.env.LOG_LEVEL || 'info',
      timestamp: () => `,"time":"${new Date().toISOString()}"`,
    },
  })

  app.register(require('./src/plugins/db'))
  app.register(require('./src/plugins/cors'))
  app.register(require('./src/plugins/static'))

  app.register(require('./src/routes/funcionarias'), { prefix: '/api' })
  app.register(require('./src/routes/registros'), { prefix: '/api' })
  app.register(require('./src/routes/exportacao'), { prefix: '/api' })

  return app
}

module.exports = buildApp
