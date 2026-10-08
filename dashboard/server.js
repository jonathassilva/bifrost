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
function loadConfig() {
  const configPath = path.join(__dirname, 'config.json')
  try {
    const raw = fs.readFileSync(configPath, 'utf-8')
    return JSON.parse(raw)
  } catch (err) {
    console.error('[server] Failed to read config.json:', err.message)
    return { directories: {} }
  }
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
  console.log(`[server] Config loaded from config.json`)
})
