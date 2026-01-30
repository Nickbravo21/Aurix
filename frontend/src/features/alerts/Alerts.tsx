/**
 * Alerts Page - Dark Theme
 */
export default function Alerts() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Alerts</h1>
          <p className="text-slate-400">Monitor important financial events</p>
        </div>

        {/* Coming Soon */}
        <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-12 text-center">
          <div className="space-y-4">
            <div className="text-6xl mb-4">🔔</div>
            <h3 className="text-2xl font-bold text-white">Alerts Coming Soon</h3>
            <p className="text-slate-400 max-w-md mx-auto">
              Smart alerts and notification rules will help you stay on top of important financial events.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
