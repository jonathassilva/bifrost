import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { PALETTE, TOOLTIP_STYLE } from './chartConfig'

export function ChartCategory({ data }) {
  // Filter out any entries that look like JSON objects or are clearly not category names
  const chartData = data
    .filter(([name]) => {
      if (!name || name === 'Unknown') return false
      // Exclude entries that look like JSON (engines_json leaking)
      if (name.startsWith('{') || name.startsWith('[')) return false
      // Exclude very long strings (not a category name)
      if (name.length > 40) return false
      return true
    })
    .map(([name, value]) => ({ name, value }))

  if (!chartData.length) {
    return (
      <div className="card flex items-center justify-center h-48 text-gray-400 text-sm">
        Sem dados de categoria disponíveis
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-title">Distribuição por categoria</div>
      <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="42%"
            innerRadius={65}
            outerRadius={100}
            paddingAngle={2}
            dataKey="value"
          >
            {chartData.map((_, i) => (
              <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
            ))}
          </Pie>
          <Tooltip
            {...TOOLTIP_STYLE}
            formatter={(value, name) => [value.toLocaleString('pt-BR'), name]}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 11, color: '#6b7280', paddingTop: 8 }}
            formatter={(value) =>
              value.length > 18 ? value.slice(0, 18) + '…' : value
            }
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
