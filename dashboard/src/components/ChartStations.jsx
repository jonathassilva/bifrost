import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { AXIS_STYLE, TOOLTIP_STYLE } from './chartConfig'

export function ChartStations({ data }) {
  const chartData = data.map(([name, value]) => ({ name, value }))

  return (
    <div className="card">
      <div className="card-title">Amostras por estação</div>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 4 }}>
          <XAxis dataKey="name" {...AXIS_STYLE} />
          <YAxis {...AXIS_STYLE} />
          <Tooltip {...TOOLTIP_STYLE} />
          <Bar dataKey="value" fill="#1D9E75" radius={[4, 4, 0, 0]} maxBarSize={60}>
            {chartData.map((_, i) => (
              <Cell
                key={i}
                fill={`hsl(${160 + i * 20}, 60%, ${40 - i * 3}%)`}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
