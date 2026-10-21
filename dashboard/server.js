import express from 'express'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const app = express()
const PORT = Number(process.env.PORT) || 3001
// Somente loopback por padrão: os dados de threat intel não devem ficar expostos na rede.
// Para expor conscientemente (ex.: VM de análise), defina HOST=0.0.0.0.
const HOST = process.env.HOST || '127.0.0.1'

// Proteção contra DNS rebinding: um site malicioso pode resolver o próprio domínio
// para 127.0.0.1 e ler a API pelo navegador da vítima. Só aceitamos Host de loopback
// (ou os nomes extras listados em ALLOWED_HOSTS, separados por vírgula).
const ALLOWED_HOSTS = new Set([
  'localhost',
  '127.0.0.1',
  '[::1]',
  ...(process.env.ALLOWED_HOSTS || '').split(',').map((h) => h.trim().toLowerCase()).filter(Boolean),
])

app.use((req, res, next) => {
  const hostname = (req.headers.host || '').toLowerCase().replace(/:\d+$/, '')
  if (!ALLOWED_HOSTS.has(hostname)) {
    return res.status(403).json({ error: 'Host not allowed' })
  }
  next()
})

// Load config.json
// Retorna sempre { directories, configStatus, configError? }, onde configStatus é
// 'ok' | 'missing' | 'invalid'. O frontend usa o status para orientar o usuário.
const CONFIG_PATH = path.join(__dirname, 'config.json')

function loadConfig() {
  const fail = (configStatus, configError) => ({ directories: {}, configStatus, configError })

  let raw
  try {
    raw = fs.readFileSync(CONFIG_PATH, 'utf-8')
  } catch (err) {
    if (err.code === 'ENOENT') {
      return fail('missing', 'config.json não encontrado. Copie config.example.json para config.json e ajuste os caminhos.')
    }
    return fail('invalid', `Não foi possível ler config.json: ${err.message}`)
  }

  let parsed
  try {
    // O Bloco de Notas do Windows salva UTF-8 com BOM, que o JSON.parse rejeita
    parsed = JSON.parse(raw.replace(/^\uFEFF/, ''))
  } catch (err) {
    return fail('invalid', `config.json não é um JSON válido (${err.message}). No Windows, escreva os caminhos com \\\\ ou /.`)
  }

  const dirs = parsed && parsed.directories
  if (!dirs || typeof dirs !== 'object' || Array.isArray(dirs)) {
    return fail('invalid', 'config.json deve conter um objeto "directories" no formato { "grupo": "caminho" }.')
  }

  // Mantém só entradas com caminho preenchido; o resto conta como "não configurado"
  const directories = {}
  for (const [group, dirPath] of Object.entries(dirs)) {
    if (typeof dirPath === 'string' && dirPath.trim()) directories[group] = dirPath
  }
  return { directories, configStatus: 'ok' }
}

// GET /api/config — return configured directories (paths only, no data)
app.get('/api/config', (req, res) => {
  const config = loadConfig()
  res.json(config)
})

// GET /api/data/:group — read all CSVs from the configured directory for that group
app.get('/api/data/:group', (req, res) => {
  const config = loadConfig()
  const group = req.params.group
  // Object.hasOwn evita resolver propriedades herdadas ("constructor", "__proto__"...)
  const directories = config.directories || {}
  const dirPath = Object.hasOwn(directories, group) ? directories[group] : undefined

  if (!dirPath) {
    return res.status(404).json({ error: `Group "${group}" not found in config.json` })
  }

  if (!fs.existsSync(dirPath)) {
    return res.status(404).json({ error: `Directory not found: ${dirPath}` })
  }

  let files
  try {
    files = fs.readdirSync(dirPath).filter((f) => f.endsWith('.csv'))
  } catch (err) {
    return res.status(500).json({ error: `Failed to read directory: ${err.message}` })
  }

  if (!files.length) {
    return res.json({ group, files: [], rows: [] })
  }

  const allRows = []
  const loadedFiles = []

  for (const file of files) {
    try {
      const content = fs.readFileSync(path.join(dirPath, file), 'utf-8')
      loadedFiles.push(file)
      // Parse CSV manually (simple split — PapaParse runs on frontend)
      // We send raw CSV text per file to let frontend parse it
      allRows.push({ name: file, content })
    } catch (err) {
      console.warn(`[server] Could not read ${file}:`, err.message)
    }
  }

  res.json({ group, files: loadedFiles, csvFiles: allRows })
})

app.listen(PORT, HOST, () => {
  console.log(`[server] API running at http://${HOST}:${PORT}`)
  if (HOST !== '127.0.0.1' && HOST !== 'localhost') {
    console.warn(`[server] ATENÇÃO: API exposta em ${HOST}. Qualquer máquina com acesso à rede pode ler os dados.`)
  }
  const { configStatus, configError, directories } = loadConfig()
  if (configStatus === 'ok') {
    console.log(`[server] config.json carregado: ${Object.keys(directories).join(', ') || 'nenhum grupo configurado'}`)
  } else {
    console.warn(`[server] ATENÇÃO: ${configError}`)
  }
})
