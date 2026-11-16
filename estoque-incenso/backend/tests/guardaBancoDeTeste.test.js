'use strict'

const { test } = require('node:test')
const assert = require('node:assert/strict')
const { garantirBancoDeTeste, BancoDeTesteInseguroError } = require('./guardaBancoDeTeste')

const bloqueia = (args) => assert.throws(() => garantirBancoDeTeste(args), BancoDeTesteInseguroError)

test('guarda — aceita Postgres em localhost', () => {
  garantirBancoDeTeste({ databaseUrl: 'postgresql://u:p@localhost:5433/estoque_incenso', nodeEnv: 'development' })
  garantirBancoDeTeste({ databaseUrl: 'postgresql://u:p@127.0.0.1:5432/x' })
})

test('guarda — bloqueia host remoto (ex.: Supabase)', () => {
  bloqueia({ databaseUrl: 'postgresql://u:p@db.abcdefgh.supabase.co:5432/postgres' })
})

test('guarda — bloqueia NODE_ENV=production mesmo com host local', () => {
  bloqueia({ databaseUrl: 'postgresql://u:p@localhost:5432/x', nodeEnv: 'production' })
})

test('guarda — bloqueia DATABASE_URL ausente ou inválida', () => {
  bloqueia({ databaseUrl: undefined })
  bloqueia({ databaseUrl: 'isso não é uma url' })
})
