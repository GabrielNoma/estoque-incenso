'use strict'

// Os testes inserem e apagam linhas: só podem rodar contra um banco local.
const HOSTS_LOCAIS = new Set(['localhost', '127.0.0.1', '[::1]'])

class BancoDeTesteInseguroError extends Error {
  constructor(motivo) {
    super(`[testes] Execução bloqueada: ${motivo}. Use um Postgres local no DATABASE_URL.`)
    this.name = 'BancoDeTesteInseguroError'
  }
}

function garantirBancoDeTeste({ databaseUrl, nodeEnv }) {
  if (nodeEnv === 'production') {
    throw new BancoDeTesteInseguroError('NODE_ENV=production')
  }
  if (!databaseUrl) {
    throw new BancoDeTesteInseguroError('DATABASE_URL não definida')
  }
  let host
  try {
    host = new URL(databaseUrl).hostname
  } catch {
    throw new BancoDeTesteInseguroError('DATABASE_URL inválida')
  }
  if (!HOSTS_LOCAIS.has(host)) {
    throw new BancoDeTesteInseguroError(`host "${host}" não é local`)
  }
}

module.exports = { garantirBancoDeTeste, BancoDeTesteInseguroError }
