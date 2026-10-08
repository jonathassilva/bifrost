import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { AXIS_STYLE, TOOLTIP_STYLE } from './chartConfig'

export function ChartLabels({ data }) {
  const chartData = [...data]
    .reverse()
    .map(([name, value]) => ({ name, value }))

  return (
    <div className="card">
      <div className="card-title">Top 10 labels de malware</div>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          layout="vertical"
          data={chartData}
          margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
        >
          <XAxis type="number" {...AXIS_STYLE} />
          <YAxis
            type="category"
            dataKey="name"
            width={160}
            tick={{ fill: '#71717a', fontSize: 11 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip {...TOOLTIP_STYLE} />
          <Bar dataKey="value" fill="#7F77DD" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
