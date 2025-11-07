/**
 * Data Sources Page - Dark Theme
 */
export default function DataSources() {
  const connectedSources = [
    { id: 1, name: 'QuickBooks Online', type: 'Accounting', status: 'Connected', icon: '📗', lastSync: '2 hours ago' },
    { id: 2, name: 'Stripe', type: 'Payment', status: 'Connected', icon: '💳', lastSync: '5 hours ago' },
  ]

  const availableSources = [
    { name: 'Xero', type: 'Accounting', icon: '📘' },
    { name: 'PayPal', type: 'Payment', icon: '💰' },
    { name: 'Square', type: 'Payment', icon: '⬜' },
    { name: 'Plaid', type: 'Banking', icon: '🏦' },
    { name: 'Shopify', type: 'E-commerce', icon: '🛍️' },
    { name: 'WooCommerce', type: 'E-commerce', icon: '🛒' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Data Sources</h1>
          <p className="text-slate-400">Connect and manage your financial data sources</p>
        </div>

        {/* Connected Sources */}
        <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
            Connected Sources
          </h2>
          <div className="space-y-4">
            {connectedSources.map((source) => (
              <div
                key={source.id}
                className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-cyan-500/50 transition-all duration-300 group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center text-2xl transform group-hover:scale-110 transition-transform shadow-lg">
                    {source.icon}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white group-hover:text-cyan-400 transition-colors">
                      {source.name}
                    </h3>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-sm text-slate-400">{source.type}</span>
                      <span className="text-slate-600">•</span>
                      <span className="text-sm text-slate-400">Last synced: {source.lastSync}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-sm font-semibold border border-emerald-500/30">
                    ✓ {source.status}
                  </span>
                  <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors text-sm font-medium">
                    🔄 Sync Now
                  </button>
                  <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors text-sm font-medium">
                    ⚙️ Configure
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Available Sources */}
        <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6">
          <h2 className="text-2xl font-bold text-white mb-4">Available Integrations</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {availableSources.map((source) => (
              <button
                key={source.name}
                className="p-6 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-cyan-500/50 rounded-lg transition-all duration-300 group text-left"
              >
                <div className="flex items-center gap-4 mb-3">
                  <div className="w-12 h-12 bg-slate-700 group-hover:bg-gradient-to-br group-hover:from-cyan-500 group-hover:to-blue-600 rounded-lg flex items-center justify-center text-2xl transition-all duration-300">
                    {source.icon}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white group-hover:text-cyan-400 transition-colors">
                      {source.name}
                    </h3>
                    <p className="text-sm text-slate-400">{source.type}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-cyan-400 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                    + Connect Now
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
