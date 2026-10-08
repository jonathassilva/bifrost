import express from 'express'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const app = express()
const PORT = 3001

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
  const dirPath = config.directories[group]

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

app.listen(PORT, () => {
  console.log(`[server] API running at http://localhost:${PORT}`)
  console.log(`[server] Config loaded from config.json`)
})
