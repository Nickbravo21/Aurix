/**
 * Financial Dashboard - Dark Professional UI
 */
import { useEffect, useState } from 'react'

export default function Dashboard() {
  const [metrics, setMetrics] = useState({
    revenue: 0,
    expenses: 0,
    netCash: 0,
    runway: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate API call with animation
    setTimeout(() => {
      setMetrics({
        revenue: 245680,
        expenses: 182340,
        netCash: 63340,
        runway: 256
      })
      setLoading(false)
    }, 800)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="relative">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-cyan-500"></div>
          <div className="absolute top-0 left-0 h-16 w-16 rounded-full border-4 border-slate-700"></div>
          <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 text-cyan-400 font-semibold text-sm whitespace-nowrap">
            Loading Dashboard...
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8 space-y-8">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-white tracking-tight bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            Financial Overview
          </h1>
          <p className="text-slate-400 mt-2 text-lg flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
            Real-time insights powered by AI
          </p>
        </div>
        <div className="flex gap-3">
          <button className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-semibold shadow-lg hover:shadow-cyan-500/20 transition-all duration-200 transform hover:scale-105 border border-slate-700">
            <span className="flex items-center gap-2">
              📊 Analytics
            </span>
          </button>
          <button className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg font-semibold shadow-lg hover:shadow-cyan-500/50 transition-all duration-200 transform hover:scale-105">
            <span className="flex items-center gap-2">
              📥 Export Report
            </span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Revenue"
          value={`$${metrics.revenue.toLocaleString()}`}
          change="+12.3%"
          trend="up"
          icon="💰"
          color="blue"
        />
        <MetricCard
          title="Total Expenses"
          value={`$${metrics.expenses.toLocaleString()}`}
          change="+5.2%"
          trend="neutral"
          icon="📊"
          color="purple"
        />
        <MetricCard
          title="Net Cash Flow"
          value={`$${metrics.netCash.toLocaleString()}`}
          change="+24.1%"
          trend="up"
          icon="📈"
          color="green"
        />
        <MetricCard
          title="Cash Runway"
          value={`${metrics.runway} days`}
          change="Healthy"
          trend="up"
          icon="⏱️"
          color="indigo"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Revenue Trend" subtitle="Last 12 months" />
        <ChartCard title="Expense Breakdown" subtitle="By category" />
      </div>

      {/* AI Insights & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <span className="relative">
                🤖
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-purple-500"></span>
                </span>
              </span>
              AI Financial Summary
            </h2>
            <span className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm rounded-full font-semibold shadow-lg shadow-purple-500/50 animate-pulse">
              AI Powered
            </span>
          </div>
          <div className="space-y-4">
            <InsightCard 
              icon="✨"
              title="Strong Cash Position"
              description="Your revenue grew 24% this month, outpacing expenses by 19 percentage points."
              color="green"
            />
            <InsightCard 
              icon="💡"
              title="Cost Optimization Opportunity"
              description="Software subscriptions increased 15%. Consider consolidating tools."
              color="yellow"
            />
            <InsightCard 
              icon="🎯"
              title="Revenue Forecast"
              description="Based on trends, projected revenue for next quarter: $820K (+18%)"
              color="blue"
            />
          </div>
        </div>

        <div className="bg-slate-900/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-slate-800">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center justify-between">
            Recent Activity
            <span className="text-xs text-slate-400 font-normal">Live</span>
          </h2>
          <div className="space-y-3">
            {[
              { type: 'payment', amount: '+$5,240', desc: 'Client Invoice #1234', time: '2h ago', icon: '💳' },
              { type: 'expense', amount: '-$890', desc: 'AWS Infrastructure', time: '5h ago', icon: '☁️' },
              { type: 'payment', amount: '+$12,500', desc: 'Contract Payment', time: '1d ago', icon: '📄' },
              { type: 'expense', amount: '-$2,400', desc: 'Team Salaries', time: '2d ago', icon: '👥' },
            ].map((transaction, i) => (
              <TransactionRow key={i} {...transaction} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function MetricCard({ title, value, change, trend, icon, color }: any) {
  const colorClasses = {
    blue: 'from-cyan-500 to-blue-600',
    purple: 'from-purple-500 to-pink-600',
    green: 'from-emerald-500 to-teal-600',
    indigo: 'from-indigo-500 to-purple-600',
  }

  const trendColors = {
    up: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    neutral: 'text-slate-400 bg-slate-500/10 border-slate-500/20',
    down: 'text-red-400 bg-red-500/10 border-red-500/20'
  }

  return (
    <div className="bg-slate-900/50 backdrop-blur-sm rounded-xl shadow-lg hover:shadow-cyan-500/20 transition-all duration-300 transform hover:-translate-y-1 border border-slate-800 overflow-hidden group">
      <div className={`h-1 bg-gradient-to-r ${colorClasses[color as keyof typeof colorClasses]} group-hover:h-2 transition-all duration-300`}></div>
      <div className="p-6 relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-cyan-500/5 to-transparent rounded-full -mr-16 -mt-16 group-hover:scale-150 transition-transform duration-500"></div>
        <div className="flex items-center justify-between mb-4 relative z-10">
          <div className="text-4xl transform group-hover:scale-110 transition-transform duration-300">{icon}</div>
          <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${trendColors[trend as keyof typeof trendColors]}`}>
            {change}
          </span>
        </div>
        <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-3 relative z-10">{title}</h3>
        <p className="text-3xl font-bold text-white relative z-10">{value}</p>
      </div>
    </div>
  )
}

function ChartCard({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="bg-slate-900/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-slate-800 hover:border-cyan-500/50 transition-all duration-300">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-white">{title}</h3>
          <p className="text-slate-400 text-sm">{subtitle}</p>
        </div>
        <div className="flex gap-2">
          <button className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
            <span className="text-slate-400">📈</span>
          </button>
          <button className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
            <span className="text-slate-400">⚙️</span>
          </button>
        </div>
      </div>
      <div className="h-72 flex items-center justify-center bg-gradient-to-br from-slate-800/50 via-slate-900/50 to-slate-800/50 rounded-xl relative overflow-hidden border border-slate-700/50">
        <div className="absolute inset-0">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 2px 2px, rgb(100 116 139 / 0.15) 1px, transparent 0)',
            backgroundSize: '32px 32px'
          }}></div>
        </div>
        <div className="relative z-10 text-center">
          <div className="text-5xl mb-3 animate-pulse">📊</div>
          <p className="text-slate-300 font-medium text-lg">Chart Visualization</p>
          <p className="text-slate-500 text-sm mt-2">Interactive charts coming soon</p>
          <div className="mt-4 flex gap-2 justify-center">
            <div className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
            <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
          </div>
        </div>
      </div>
    </div>
  )
}

function InsightCard({ icon, title, description, color }: any) {
  const borderColors = {
    green: 'border-l-emerald-500 bg-emerald-500/5',
    yellow: 'border-l-yellow-500 bg-yellow-500/5',
    blue: 'border-l-cyan-500 bg-cyan-500/5',
  }

  return (
    <div className={`border-l-4 ${borderColors[color as keyof typeof borderColors]} backdrop-blur-sm p-4 rounded-r-lg hover:bg-slate-800/30 transition-all duration-300 border border-slate-800 border-l-4`}>
      <div className="flex items-start space-x-3">
        <span className="text-2xl flex-shrink-0">{icon}</span>
        <div>
          <h4 className="font-semibold text-white mb-1">{title}</h4>
          <p className="text-slate-400 text-sm">{description}</p>
        </div>
      </div>
    </div>
  )
}

function TransactionRow({ amount, desc, time, icon }: any) {
  const isPositive = amount.startsWith('+')
  
  return (
    <div className="flex items-center justify-between p-3 bg-slate-800/30 backdrop-blur-sm rounded-lg hover:bg-slate-800/50 transition-all duration-200 cursor-pointer border border-slate-700/50 hover:border-cyan-500/30 group">
      <div className="flex items-center space-x-3">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${isPositive ? 'bg-emerald-500/20 group-hover:bg-emerald-500/30' : 'bg-red-500/20 group-hover:bg-red-500/30'}`}>
          <span className="transform group-hover:scale-110 transition-transform">{icon}</span>
        </div>
        <div>
          <p className="font-medium text-white text-sm group-hover:text-cyan-400 transition-colors">{desc}</p>
          <p className="text-xs text-slate-500">{time}</p>
        </div>
      </div>
      <p className={`font-bold text-sm ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>{amount}</p>
    </div>
  )
}
