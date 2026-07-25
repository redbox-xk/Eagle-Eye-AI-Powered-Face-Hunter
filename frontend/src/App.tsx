import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Agents from './pages/Agents'
import Memory from './pages/Memory'
import Knowledge from './pages/Knowledge'
import Reasoning from './pages/Reasoning'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="agents" element={<Agents />} />
        <Route path="memory" element={<Memory />} />
        <Route path="knowledge" element={<Knowledge />} />
        <Route path="reasoning" element={<Reasoning />} />
      </Route>
    </Routes>
  )
}
