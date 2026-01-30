import { useState } from 'react'

export default function DataLab() {
  const [uploading, setUploading] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) return
    
    setUploading(true)
    // TODO: Implement actual upload to backend
    setTimeout(() => {
      setUploading(false)
      alert('Upload functionality will be connected to backend with your GPT API key')
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
            <span className="text-5xl">🧠</span>
            AI Data Lab
          </h1>
          <p className="text-slate-400 text-lg">
            Upload Google Sheets data (CSV) and get AI-powered insights
          </p>
        </div>

        {/* Upload Area */}
        <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6 mb-6">
          <h2 className="text-xl font-bold text-white mb-4">Upload Dataset</h2>
          
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${
              dragActive
                ? 'border-cyan-500 bg-cyan-500/10'
                : 'border-slate-700 bg-slate-900/30'
            }`}
          >
            {file ? (
              <div className="space-y-4">
                <div className="text-6xl">📄</div>
                <div>
                  <p className="text-xl font-bold text-white mb-1">{file.name}</p>
                  <p className="text-slate-400">{(file.size / 1024).toFixed(2)} KB</p>
                </div>
                <div className="flex gap-3 justify-center">
                  <button
                    onClick={handleUpload}
                    disabled={uploading}
                    className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg font-semibold shadow-lg shadow-cyan-500/30 transition-all duration-200 transform hover:scale-105 disabled:opacity-50"
                  >
                    {uploading ? 'Uploading...' : '📤 Upload & Analyze'}
                  </button>
                  <button
                    onClick={() => setFile(null)}
                    className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-semibold transition-all duration-200"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-6xl mb-4">📊</div>
                <h3 className="text-2xl font-bold text-white">Drop your CSV file here</h3>
                <p className="text-slate-400">or</p>
                <label className="inline-block">
                  <input
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <span className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg font-semibold shadow-lg shadow-cyan-500/30 transition-all duration-200 transform hover:scale-105 cursor-pointer inline-block">
                    📂 Browse Files
                  </span>
                </label>
                <p className="text-sm text-slate-500 mt-4">Supported formats: CSV, XLSX, XLS</p>
              </div>
            )}
          </div>
        </div>

        {/* Info Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6">
            <div className="text-3xl mb-3">🔍</div>
            <h3 className="text-lg font-bold text-white mb-2">AI Analysis</h3>
            <p className="text-sm text-slate-400">
              Get GPT-powered insights about your financial data automatically
            </p>
          </div>
          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6">
            <div className="text-3xl mb-3">📈</div>
            <h3 className="text-lg font-bold text-white mb-2">Visualizations</h3>
            <p className="text-sm text-slate-400">
              Interactive charts and graphs to understand your data better
            </p>
          </div>
          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6">
            <div className="text-3xl mb-3">💬</div>
            <h3 className="text-lg font-bold text-white mb-2">Ask Questions</h3>
            <p className="text-sm text-slate-400">
              Query your data in natural language and get instant answers
            </p>
          </div>
        </div>

        {/* Note about API Key */}
        <div className="mt-6 bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
          <p className="text-yellow-400 text-sm">
            <strong>Note:</strong> You'll need to add your OpenAI API key in settings to enable AI analysis features.
          </p>
        </div>
      </div>
    </div>
  )
}
