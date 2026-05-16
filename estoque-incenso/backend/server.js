'use strict'

if (process.env.NODE_ENV !== 'production') {
  require('dotenv').config()
}

const buildApp = require('./app')

const app = buildApp()

app.listen({ port: Number(process.env.PORT) || 3000, host: '0.0.0.0' }, (err, address) => {
  if (err) {
    app.log.error(err)
    process.exit(1)
  }
  app.log.info(`Servidor rodando em ${address}`)
})
