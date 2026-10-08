import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  CartesianGrid, ResponsiveContainer, Area, AreaChart,
} from 'recharts'
import { AXIS_STYLE, GRID_STYLE, TOOLTIP_STYLE } from './chartConfig'

export function ChartTimeline({ data }) {
  const chartData = data.map(([date, value]) => ({ date, value }))

  return (
    <div className="card">
      <div className="card-title">Volume de scans por dia</div>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 4 }}>
          <defs>
            <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#378ADD" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#378ADD" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid {...GRID_STYLE} />
          <XAxis
            dataKey="date"
            {...AXIS_STYLE}
            tick={{ fill: '#52525b', fontSize: 10 }}
            angle={-30}
            textAnchor="end"
            height={40}
            interval="preserveStartEnd"
          />
          <YAxis {...AXIS_STYLE} />
          <Tooltip {...TOOLTIP_STYLE} />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#378ADD"
            strokeWidth={2}
            fill="url(#scanGrad)"
            dot={false}
            activeDot={{ r: 4, fill: '#378ADD' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
