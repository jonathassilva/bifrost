export function KpiCards({ metrics, fileCount }) {
  const cards = [
    {
      label: 'Total de amostras',
      value: metrics.total.toLocaleString('pt-BR'),
      sub: `${fileCount} arquivo(s) carregado(s)`,
    },
    {
      label: 'Detecção média',
      value: `${metrics.avgDetection.toFixed(1)}%`,
      sub: 'positivos / total de engines',
      accent:
        metrics.avgDetection >= 70 ? 'text-red-500'
        : metrics.avgDetection >= 40 ? 'text-yellow-500'
        : 'text-emerald-600',
    },
    {
      label: 'Categorias únicas',
      value: metrics.uniqueCategories,
      sub: 'tipos de ameaça distintos',
    },
    {
      label: 'Engines ativos',
      value: metrics.uniqueEngines,
      sub: 'engines que detectaram algo',
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      {cards.map((c) => (
        <div key={c.label} className="kpi-card">
          <div className="kpi-label">{c.label}</div>
          <div className={`kpi-value ${c.accent || 'text-zinc-800'}`}>{c.value}</div>
          <div className="kpi-sub">{c.sub}</div>
        </div>
      ))}
    </div>
  )
}
