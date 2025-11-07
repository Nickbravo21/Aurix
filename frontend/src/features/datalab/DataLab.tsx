import { useState } from 'react'

export default function DataLab() {
  const [uploading, setUploading] = useState(false)

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
            <span className="text-5xl">🧠</span>
            AI Data Lab
          </h1>
          <p className="text-slate-400 text-lg">
            Upload datasets, run AI analysis, and ask questions in natural language
          </p>
        </div>

        <div className="border-2 border-dashed border-slate-700 rounded-xl p-12 text-center bg-slate-900/50">
          <div className="space-y-4">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-2xl font-bold text-white">AI Data Lab Coming Soon</h3>
            <p className="text-slate-400">Upload CSV files and get AI-powered insights</p>
          </div>
        </div>
      </div>
    </div>
  )
}
