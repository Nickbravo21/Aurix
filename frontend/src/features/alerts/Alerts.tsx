/**
 * Alerts Page - Dark Theme
 */
export default function Alerts() {
  const alerts = [
    { id: 1, title: 'High Expense Alert', message: 'Marketing spend exceeded budget by 15%', time: '2 hours ago', type: 'warning', icon: '⚠️' },
    { id: 2, title: 'Payment Received', message: 'Invoice #1234 paid - $5,240', time: '5 hours ago', type: 'success', icon: '✅' },
    { id: 3, title: 'Low Cash Warning', message: 'Cash balance below threshold', time: '1 day ago', type: 'critical', icon: '🚨' },
    { id: 4, title: 'Forecast Update', message: 'Revenue forecast updated for Q1 2025', time: '2 days ago', type: 'info', icon: 'ℹ️' },
  ]

  const alertRules = [
    { id: 1, name: 'Cash Flow Alert', condition: 'Balance < $10,000', active: true },
    { id: 2, name: 'Large Transaction', condition: 'Amount > $5,000', active: true },
    { id: 3, name: 'Budget Exceeded', condition: 'Spend > Budget + 10%', active: false },
  ]

  const getAlertStyle = (type: string) => {
    switch (type) {
      case 'critical':
        return 'bg-red-500/10 border-red-500/30 hover:border-red-500/50'
      case 'warning':
        return 'bg-yellow-500/10 border-yellow-500/30 hover:border-yellow-500/50'
      case 'success':
        return 'bg-emerald-500/10 border-emerald-500/30 hover:border-emerald-500/50'
      default:
        return 'bg-cyan-500/10 border-cyan-500/30 hover:border-cyan-500/50'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
              Alerts
              <span className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm font-semibold border border-red-500/30">
                3 New
              </span>
            </h1>
            <p className="text-slate-400">Monitor important financial events</p>
          </div>
          <button className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg font-semibold shadow-lg shadow-cyan-500/30 transition-all duration-200 transform hover:scale-105">
            + Create Alert Rule
          </button>
        </div>

        {/* Recent Alerts */}
        <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6">
          <h2 className="text-2xl font-bold text-white mb-4">Recent Alerts</h2>
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 border rounded-lg transition-all duration-300 cursor-pointer group ${getAlertStyle(alert.type)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="text-3xl">{alert.icon}</div>
                    <div>
                      <h3 className="text-lg font-semibold text-white group-hover:text-cyan-400 transition-colors">
                        {alert.title}
                      </h3>
                      <p className="text-slate-400 mt-1">{alert.message}</p>
                      <span className="text-sm text-slate-500 mt-2 inline-block">{alert.time}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
                      <span className="text-slate-400">👁️</span>
                    </button>
                    <button className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
                      <span className="text-slate-400">✓</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Alert Rules */}
        <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6">
          <h2 className="text-2xl font-bold text-white mb-4">Alert Rules</h2>
          <div className="space-y-3">
            {alertRules.map((rule) => (
              <div
                key={rule.id}
                className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-cyan-500/50 transition-all duration-300 group"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-2xl ${
                    rule.active ? 'bg-gradient-to-br from-cyan-500 to-blue-600' : 'bg-slate-700'
                  }`}>
                    {rule.active ? '🔔' : '🔕'}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white group-hover:text-cyan-400 transition-colors">
                      {rule.name}
                    </h3>
                    <p className="text-sm text-slate-400">Condition: {rule.condition}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" checked={rule.active} className="sr-only peer" readOnly />
                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-cyan-600 peer-checked:to-blue-600"></div>
                  </label>
                  <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors text-sm font-medium">
                    ⚙️ Edit
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
