'use strict'

const { execSync, spawn } = require('child_process')
const path = require('path')

const root = __dirname
const backend = path.join(root, 'backend')
const frontend = path.join(root, 'frontend')

function log(msg, color) {
  const colors = { cyan: '\x1b[36m', green: '\x1b[32m', yellow: '\x1b[33m', red: '\x1b[31m', reset: '\x1b[0m' }
  console.log(`${colors[color] || ''}${msg}${colors.reset}`)
}

log('\n============================================', 'cyan')
log('  Estoque Incenso — Dev Startup', 'cyan')
log('============================================\n', 'cyan')

// 1. Testes
log('[1/3] Rodando testes...', 'yellow')
try {
  execSync('npm test', { cwd: backend, stdio: 'inherit' })
  log('\nTodos os testes passaram.\n', 'green')
} catch {
  log('\nTESTES FALHARAM — aplicação não será iniciada.', 'red')
  process.exit(1)
}

// 2. Backend
log('[2/3] Iniciando backend  → http://localhost:3000', 'yellow')
const back = spawn('node', ['server.js'], { cwd: backend, stdio: 'inherit' })
back.on('error', err => { log(`Backend erro: ${err.message}`, 'red'); process.exit(1) })

// 3. Frontend
log('[3/3] Iniciando frontend → http://localhost:4200', 'yellow')
const front = spawn('npm', ['start'], { cwd: frontend, stdio: 'inherit', shell: true })
front.on('error', err => { log(`Frontend erro: ${err.message}`, 'red'); process.exit(1) })

log('\n============================================', 'green')
log('  API + Angular prod:  http://localhost:3000', 'green')
log('  Angular dev (HMR):   http://localhost:4200', 'green')
log('============================================\n', 'green')

process.on('SIGINT', () => {
  back.kill()
  front.kill()
  process.exit(0)
})
