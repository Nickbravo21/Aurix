/**
 * Reports Page - Dark Theme
 */
export default function Reports() {
  const reports = [
    { id: 1, name: 'Monthly Financial Summary', date: '2025-11-01', status: 'Ready', icon: '📊', color: 'cyan' },
    { id: 2, name: 'Q4 2024 Analysis', date: '2025-10-31', status: 'Ready', icon: '📈', color: 'blue' },
    { id: 3, name: 'Tax Preparation Report', date: '2025-10-15', status: 'Processing', icon: '📋', color: 'purple' },
    { id: 4, name: 'Cash Flow Projection', date: '2025-10-01', status: 'Ready', icon: '💰', color: 'green' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Reports</h1>
            <p className="text-slate-400">Generate and view financial reports</p>
          </div>
          <button className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg font-semibold shadow-lg shadow-cyan-500/30 transition-all duration-200 transform hover:scale-105">
            + Generate New Report
          </button>
        </div>

        {/* Report Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {reports.map((report) => (
            <div
              key={report.id}
              className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6 hover:border-cyan-500/50 transition-all duration-300 cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center text-2xl transform group-hover:scale-110 transition-transform">
                    {report.icon}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white group-hover:text-cyan-400 transition-colors">
                      {report.name}
                    </h3>
                    <p className="text-sm text-slate-400">Generated: {report.date}</p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  report.status === 'Ready' 
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                    : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                }`}>
                  {report.status}
                </span>
              </div>
              <div className="flex gap-2 mt-4">
                <button className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors text-sm font-medium">
                  👁️ View
                </button>
                <button className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors text-sm font-medium">
                  📥 Download
                </button>
                <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors text-sm font-medium">
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Report Templates */}
        <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6">
          <h2 className="text-2xl font-bold text-white mb-4">Report Templates</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {['Income Statement', 'Balance Sheet', 'Cash Flow', 'Budget vs Actual', 'Expense Analysis', 'Revenue Breakdown'].map((template) => (
              <button
                key={template}
                className="p-4 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-cyan-500/50 rounded-lg text-left transition-all duration-300 group"
              >
                <span className="text-white font-medium group-hover:text-cyan-400 transition-colors">{template}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
