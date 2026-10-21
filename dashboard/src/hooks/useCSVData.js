import { useState, useMemo, useEffect } from 'react'
import Papa from 'papaparse'

function parsePositives(val) {
  const parts = (val || '').split('/')
  const pos = parseInt(parts[0]) || 0
  const total = parseInt(parts[1]) || 1
  return { pos, total, pct: (pos / total) * 100 }
}

function getStation(loc) {
  const m = (loc || '').match(/(ST\d+)/i)
  return m ? m[1].toUpperCase() : 'Unknown'
}

function computeMetrics(allRows) {
  if (!allRows.length) return null

  let sumPct = 0
  const categories = {}, types = {}, stations = {}, engines = {}, labels = {}, dateMap = {}

  allRows.forEach((r) => {
    const { pct } = parsePositives(r.positives)
    sumPct += pct

    // Strictly use only the 'category' column — no fallback to other fields
    const rawCat = (r.category || '').trim()
    const cat = rawCat.length > 0 && !rawCat.startsWith('{') ? rawCat : 'Sem categoria'
    categories[cat] = (categories[cat] || 0) + 1

    const t = r.type || 'Unknown'
    types[t] = (types[t] || 0) + 1

    const st = getStation(r.location || r.local_location)
    stations[st] = (stations[st] || 0) + 1

    const lbl = r.best_label || 'Unknown'
    labels[lbl] = (labels[lbl] || 0) + 1

    try {
      const eng = JSON.parse(r.engines_json || '{}')
      Object.keys(eng).forEach((e) => { engines[e] = (engines[e] || 0) + 1 })
    } catch (_) {}

    const scandate = r['scandate(GMT)'] || r.scandate || ''
    if (scandate) {
      const d = scandate.split(' ')[0]
      dateMap[d] = (dateMap[d] || 0) + 1
    }
  })

  const total = allRows.length
  return {
    total,
    avgDetection: total ? sumPct / total : 0,
    uniqueCategories: Object.keys(categories).length,
    uniqueEngines: Object.keys(engines).length,
    topCategories: Object.entries(categories).sort((a, b) => b[1] - a[1]),
    topTypes: Object.entries(types).sort((a, b) => b[1] - a[1]),
    topStations: Object.entries(stations).sort((a, b) => b[1] - a[1]),
    topEngines: Object.entries(engines).sort((a, b) => b[1] - a[1]).slice(0, 10),
    topLabels: Object.entries(labels).sort((a, b) => b[1] - a[1]).slice(0, 10),
    sortedDates: Object.entries(dateMap).sort((a, b) => a[0].localeCompare(b[0])),
  }
}

function parseCSVFiles(csvFiles) {
  const allRows = []
  for (const { content } of csvFiles) {
    const result = Papa.parse(content, { header: true, skipEmptyLines: true })
    allRows.push(...result.data)
  }
  return allRows
}

export function useCSVData() {
  const [config, setConfig] = useState(null)
  const [androidData, setAndroidData] = useState({ status: 'idle', files: [], rows: [] })
  const [generalData, setGeneralData] = useState({ status: 'idle', files: [], rows: [] })

  // (Re)carrega o config.json pela API. Chamado na montagem e pelo botão Recarregar,
  // para que edições no config.json valham sem reiniciar o servidor.
  function fetchConfig() {
    fetch('/api/config')
      .then((r) => r.json())
      .then(setConfig)
      .catch(() =>
        setConfig({
          directories: {},
          configStatus: 'invalid',
          configError: 'Não foi possível contactar a API. O servidor (node server.js) está rodando?',
        })
      )
  }

  // Load config on mount
  useEffect(fetchConfig, [])

  // Load data for a group
  async function loadGroup(group, setter) {
    setter((prev) => ({ ...prev, status: 'loading' }))
    try {
      const res = await fetch(`/api/data/${group}`)
      const data = await res.json()
      if (!res.ok) throw new Error(data.error)
      const rows = parseCSVFiles(data.csvFiles || [])
      setter({ status: 'ok', files: data.files || [], rows })
    } catch (err) {
      setter({ status: 'error', error: err.message, files: [], rows: [] })
    }
  }

  // Grupo ausente do config.json não é erro: fica "não configurado" e não gera requisição
  function loadOrSkip(cfg, group, setter) {
    const directories = (cfg && cfg.directories) || {}
    if (Object.hasOwn(directories, group)) {
      loadGroup(group, setter)
    } else {
      setter({ status: 'unconfigured', files: [], rows: [] })
    }
  }

  // Load groups whenever the config is (re)loaded
  useEffect(() => {
    if (!config) return
    loadOrSkip(config, 'android-malware', setAndroidData)
    loadOrSkip(config, 'general-malware', setGeneralData)
  }, [config])

  const androidMetrics = useMemo(() => computeMetrics(androidData.rows), [androidData.rows])
  const generalMetrics = useMemo(() => computeMetrics(generalData.rows), [generalData.rows])
  const consolidatedMetrics = useMemo(
    () => computeMetrics([...androidData.rows, ...generalData.rows]),
    [androidData.rows, generalData.rows]
  )

  // Relê o config.json; o efeito acima recarrega os grupos em seguida
  function reload() {
    fetchConfig()
  }

  return {
    config,
    androidData,
    generalData,
    androidMetrics,
    generalMetrics,
    consolidatedMetrics,
    reload,
  }
}
