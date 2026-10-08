export function DirectoryStatus({ config, androidData, generalData, onReload }) {
  const dirs = config?.directories || {}

  const StatusBadge = ({ status }) => {
    const map = {
      idle:    { label: 'Aguardando', cls: 'text-gray-400' },
      loading: { label: 'Carregando…', cls: 'text-yellow-500 animate-pulse' },
      ok:      { label: 'OK', cls: 'text-emerald-600' },
      error:   { label: 'Erro', cls: 'text-red-500' },
    }
    const s = map[status] || map.idle
    return <span className={`text-xs font-mono ${s.cls}`}>{s.label}</span>
  }

  const rows = [
    { key: 'android-malware', label: 'Android Malware', data: androidData, path: dirs['android-malware'] },
    { key: 'general-malware', label: 'General Malware', data: generalData, path: dirs['general-malware'] },
  ]

  return (
    <div className="mb-6 border border-gray-200 rounded-xl overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
        <span className="text-xs font-mono text-gray-500 uppercase tracking-widest">
          Diretórios configurados
        </span>
        <button onClick={onReload}
          className="text-xs text-gray-400 hover:text-gray-700 transition-colors font-mono"
          title="Recarregar dados">
          ↺ Recarregar
        </button>
      </div>

      {rows.map(({ key, label, data, path }) => (
        <div key={key}
          className="flex flex-col sm:flex-row sm:items-center justify-between px-4 py-3 border-b border-gray-100 last:border-0 gap-1 bg-white">
          <div>
            <span className="text-xs text-gray-700 font-medium">{label}</span>
            <p className="text-xs font-mono text-gray-400 mt-0.5 break-all">
              {path || 'Não configurado'}
            </p>
            {data.status === 'error' && (
              <p className="text-xs text-red-500 mt-0.5">{data.error}</p>
            )}
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {data.status === 'ok' && (
              <span className="text-xs text-gray-400 font-mono">
                {data.files.length} CSV(s) · {data.rows.length.toLocaleString('pt-BR')} amostras
              </span>
            )}
            <StatusBadge status={data.status} />
          </div>
        </div>
      ))}
    </div>
  )
}
