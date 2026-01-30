/**
 * Reports Page - Dark Theme
 */
export default function Reports() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Reports</h1>
          <p className="text-slate-400">Generate and view financial reports</p>
        </div>

        {/* Coming Soon */}
        <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-12 text-center">
          <div className="space-y-4">
            <div className="text-6xl mb-4">📄</div>
            <h3 className="text-2xl font-bold text-white">Reports Coming Soon</h3>
            <p className="text-slate-400 max-w-md mx-auto">
              Automated report generation with AI-powered insights will be available soon.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
