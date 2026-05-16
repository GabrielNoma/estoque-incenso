'use strict'

require('dotenv').config({ path: require('path').join(__dirname, '../.env') })

const buildApp = require('../app')

async function buildTestApp() {
  const app = buildApp()
  await app.ready()
  return app
}

async function withApp(fn) {
  const app = await buildTestApp()
  try {
    await fn(app)
  } finally {
    await app.close()
  }
}

module.exports = { buildTestApp, withApp }
