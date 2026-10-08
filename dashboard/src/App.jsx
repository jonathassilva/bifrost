import { useState } from 'react'
import { useCSVData } from './hooks/useCSVData'
import { DirectoryStatus } from './components/DirectoryStatus'
import { KpiCards } from './components/KpiCards'
import { ChartCategory } from './components/ChartCategory'
import { ChartType } from './components/ChartType'
import { ChartEngines } from './components/ChartEngines'
import { ChartStations } from './components/ChartStations'
import { ChartLabels } from './components/ChartLabels'
import { ChartTimeline } from './components/ChartTimeline'

const TABS = [
  { id: 'android', label: '🤖 Android' },
  { id: 'general', label: '🛡️ Geral' },
  { id: 'consolidated', label: '📊 Consolidado' },
]

function DashboardContent({ metrics, fileCount, emptyMessage }) {
  if (!metrics) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-gray-400">
        <div className="text-5xl mb-4">🔍</div>
        <p className="text-sm">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <>
      <KpiCards metrics={metrics} fileCount={fileCount} />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <ChartCategory data={metrics.topCategories} />
        <ChartType data={metrics.topTypes} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <ChartEngines data={metrics.topEngines} />
        <ChartStations data={metrics.topStations} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <ChartLabels data={metrics.topLabels} />
        <ChartTimeline data={metrics.sortedDates} />
      </div>
    </>
  )
}

export default function App() {
  const [activeTab, setActiveTab] = useState('android')
  const {
    config, androidData, generalData,
    androidMetrics, generalMetrics, consolidatedMetrics, reload,
  } = useCSVData()

  const totalSamples = (androidData.rows?.length || 0) + (generalData.rows?.length || 0)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white px-6 py-4 flex items-center justify-between shadow-sm">
        <div>
          <h1 className="text-sm font-mono font-semibold text-gray-700 tracking-widest uppercase">
            Malware Analysis Dashboard
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Dados processados localmente — nenhum arquivo é enviado a servidores externos
          </p>
        </div>
        <div className="text-xs font-mono text-gray-400">
          {totalSamples > 0
            ? `${totalSamples.toLocaleString('pt-BR')} amostras totais`
            : 'Carregando dados…'}
        </div>
      </header>

      <main className="px-6 py-6 max-w-7xl mx-auto">
        <DirectoryStatus
          config={config}
          androidData={androidData}
          generalData={generalData}
          onReload={reload}
        />

        <div className="flex gap-1 mb-6 border-b border-gray-200">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-400 hover:text-gray-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === 'android' && (
          <DashboardContent metrics={androidMetrics} fileCount={androidData.files?.length || 0}
            emptyMessage="Nenhum dado Android carregado. Verifique o diretório em config.json." />
        )}
        {activeTab === 'general' && (
          <DashboardContent metrics={generalMetrics} fileCount={generalData.files?.length || 0}
            emptyMessage="Nenhum dado geral carregado. Verifique o diretório em config.json." />
        )}
        {activeTab === 'consolidated' && (
          <DashboardContent metrics={consolidatedMetrics}
            fileCount={(androidData.files?.length || 0) + (generalData.files?.length || 0)}
            emptyMessage="Nenhum dado carregado. Verifique os diretórios em config.json." />
        )}
      </main>
    </div>
  )
}
