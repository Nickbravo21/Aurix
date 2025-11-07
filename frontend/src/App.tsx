/**
 * Main App Component
 */
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Layout from './components/Layout'
import Login from './features/auth/Login'
import Dashboard from './features/dashboards/Dashboard'
import Reports from './features/reports/Reports'
import DataSources from './features/datasources/DataSources'
import Alerts from './features/alerts/Alerts'
import Settings from './features/settings/Settings'

function App() {
  const { user } = useAuthStore()

  if (!user) {
    return <Login />
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/datasources" element={<DataSources />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/settings/*" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App
