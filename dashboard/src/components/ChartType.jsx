import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { PALETTE, AXIS_STYLE, GRID_STYLE, TOOLTIP_STYLE } from './chartConfig'

export function ChartType({ data }) {
  const chartData = data.map(([name, value]) => ({ name, value }))

  return (
    <div className="card">
      <div className="card-title">Tipo de arquivo</div>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 4 }}>
          <XAxis dataKey="name" {...AXIS_STYLE} />
          <YAxis {...AXIS_STYLE} />
          <Tooltip {...TOOLTIP_STYLE} />
          <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={60}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
