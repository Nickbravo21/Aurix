/**
 * Main App Component
 */
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './features/dashboards/Dashboard'
import Reports from './features/reports/Reports'
import DataSources from './features/datasources/DataSources'
import Alerts from './features/alerts/Alerts'
import Settings from './features/settings/Settings'
import DataLab from './features/datalab/DataLab'
import AIChat from './features/chat/AIChat'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/datalab" element={<DataLab />} />
        <Route path="/chat" element={<AIChat />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/datasources" element={<DataSources />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/settings/*" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App
