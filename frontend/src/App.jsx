
import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000/api/overview/'

const navigation = [
  { title: 'Overview', icon: 'O' },
  { title: 'Camera Monitoring', icon: 'C' },
  { title: 'Customer Tracking', icon: 'T' },
  { title: 'Counter Interactions', icon: 'I' },
  { title: 'Alert History', icon: 'A' },
  { title: 'Settings', icon: 'S' },
]

function App() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [activePage, setActivePage] = useState('Overview')

  useEffect(() => {
    let cancelled = false

    async function loadDashboard() {
      try {
        const response = await fetch(API_URL)
        if (!response.ok) throw new Error(`Django returned HTTP ${response.status}`)
        const result = await response.json()
        if (!cancelled) {
          setData(result)
          setError('')
        }
      } catch (err) {
        if (!cancelled) setError(err.message || 'Could not connect to Django')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadDashboard()
    const intervalId = window.setInterval(loadDashboard, 10000)
    return () => {
      cancelled = true
      window.clearInterval(intervalId)
    }
  }, [])

  const sources = data?.video_sources ?? []
  const measurements = data?.recent_measurements ?? []
  const alerts = data?.recent_alerts ?? []
  const counters = data?.counters ?? []
  const latest = measurements.find(item => item.is_valid)

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">Q</div>
          <div><h2>QueueWatch</h2><p>Queue Management</p></div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <nav className="navigation">
          {navigation.map(item => (
            <button
              key={item.title}
              type="button"
              onClick={() => setActivePage(item.title)}
              className={`nav-item ${activePage === item.title ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.title}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="system-indicator">
            <span /> {error ? 'Backend connection failed' : loading ? 'Connecting to backend' : 'Dashboard API connected'}
          </div>
          <div className="profile">
            <div className="avatar">U</div>
            <div><strong>Current User</strong><p>Role not connected</p></div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">Workspace / {activePage}</div>
          <div className="topbar-right">
            <span className="connection-status">
              <span /> {error ? 'Backend not connected' : loading ? 'Connecting...' : 'Backend connected'}
            </span>
            <span className="user-button">User account</span>
          </div>
        </header>

        <section className="page-content">
          <div className="page-heading">
            <div>
              <p className="eyebrow">QUEUE OPERATIONS</p>
              <h1>{activePage === 'Overview' ? 'Dashboard Overview' : activePage}</h1>
              <p className="page-description">
                {activePage === 'Overview' && 'Monitor video sources, queue estimates and system alerts.'}
                {activePage === 'Camera Monitoring' && 'View the processed video and registered video sources.'}
                {activePage === 'Customer Tracking' && 'Review saved detector estimates. These are not verified customer identities.'}
                {activePage === 'Counter Interactions' && 'Review registered counters and their current status.'}
                {activePage === 'Alert History' && 'Review alerts returned by the Django database.'}
                {activePage === 'Settings' && 'Review the current application connection settings.'}
              </p>
            </div>
            <div className="date-chip">
              {loading ? 'Loading data...' : error ? 'Connection unavailable' : 'Refreshes every 10 seconds'}
            </div>
          </div>

          {error && (
            <div className="notice">
              <span className="notice-icon">!</span>
              <div><strong>Unable to load dashboard data</strong><p>{error}. Check that Django is running on port 8000.</p></div>
            </div>
          )}

          {!error && !loading && (
            <div className="notice">
              <span className="notice-icon">i</span>
              <div><strong>Live database connection</strong><p>Data is loaded from your Django API.</p></div>
            </div>
          )}

          {activePage === 'Overview' && (
            <>
              <div className="section-heading">
                <div><h2>System summary</h2><p>Values loaded from the Django database.</p></div>
              </div>

              <div className="summary-grid">
                <SummaryCard icon="C" label="Camera sources" value={loading ? '...' : sources.length} detail={`${sources.filter(s => s.is_active).length} active sources`} tone="blue" />
                <SummaryCard icon="Q" label="Latest unverified contour estimate" value={latest ? latest.occupancy_estimate ?? '-' : '-'} detail="Not a verified customer count" tone="purple" />
                <SummaryCard icon="A" label="Active alerts" value={loading ? '...' : alerts.filter(a => a.status === 'ACTIVE').length} detail={`${alerts.length} recent alerts`} tone="orange" />
                <SummaryCard icon="M" label="Detector-valid measurements" value={loading ? '...' : measurements.filter(m => m.is_valid).length} detail="Among the latest records" tone="green" />
              </div>

              <DataTable title="Camera sources" description="Registered video sources" headers={['SOURCE', 'TYPE', 'STATUS']} rows={sources.map(s => [s.name, s.source_type, s.is_active ? 'Active' : 'Inactive'])} />
              <DataTable title="Recent queue measurements" description="Saved detector results" headers={['SOURCE', 'ESTIMATE', 'STATUS', 'MEASURED AT']} rows={measurements.map(m => [m.video_source_name, m.occupancy_estimate ?? '-', m.status, m.measured_at ? new Date(m.measured_at).toLocaleString() : '-'])} />
              <DataTable title="Recent alerts" description="Queue threshold notifications" headers={['SOURCE', 'QUEUE', 'STATUS']} rows={alerts.map(a => [a.video_source_name, `${a.queue_count} / ${a.threshold}`, a.status])} />
            </>
          )}

          {activePage === 'Camera Monitoring' && (
            <>
              <section className="panel video-panel">
                <div className="panel-heading">
                  <div><h2>Queue video monitoring</h2><p>Processed recording with foreground detections</p></div>
                  <span className="muted-tag">Recorded video</span>
                </div>
                <div className="video-container">
                  <video className="processed-video" controls preload="metadata" playsInline src="/queue-output-v4.mp4">
                    Your browser does not support video playback.
                  </video>
                </div>
                <p className="video-disclaimer">
                  Red boxes show foreground regions, not verified individual customer detections.
                </p>
              </section>
              <DataTable title="Registered video sources" description="Sources from Django" headers={['SOURCE', 'TYPE', 'STATUS']} rows={sources.map(s => [s.name, s.source_type, s.is_active ? 'Active' : 'Inactive'])} />
            </>
          )}

          {activePage === 'Customer Tracking' && (
            <DataTable title="Detection estimates" description="These records do not identify or track unique people." headers={['SOURCE', 'ESTIMATE', 'VALIDITY', 'TIME']} rows={measurements.map(m => [m.video_source_name, m.occupancy_estimate ?? '-', m.is_valid ? 'Passed detector checks' : 'Invalid', m.measured_at ? new Date(m.measured_at).toLocaleString() : '-'])} />
          )}

          {activePage === 'Counter Interactions' && (
            <DataTable title="Registered counters" description="Counter data returned by Django" headers={['COUNTER', 'STATUS']} rows={counters.map(c => [c.name, c.status])} />
          )}

          {activePage === 'Alert History' && (
            <DataTable title="Alert history" description="Alerts returned by Django" headers={['SOURCE', 'QUEUE COUNT', 'THRESHOLD', 'STATUS']} rows={alerts.map(a => [a.video_source_name, a.queue_count, a.threshold, a.status])} />
          )}

          {activePage === 'Settings' && (
            <section className="panel">
              <div className="panel-heading"><div><h2>Application settings</h2><p>Current connection information</p></div></div>
              <div className="empty-state">
                <h3>Backend API</h3>
                <p>{API_URL}</p>
                <p>Automatic data refresh: every 10 seconds</p>
                <p>Video output: /queue-output-v4.mp4</p>
                <p>Detection method: rule-based foreground contours</p>
              </div>
            </section>
          )}

          <footer className="footer">
            <span>QueueWatch - Rule-Based Queue Management</span>
            <span>Conventional computer vision - No AI/ML models</span>
          </footer>
        </section>
      </main>
    </div>
  )
}

function SummaryCard({ icon, label, value, detail, tone }) {
  return (
    <article className="summary-card">
      <div className={`summary-icon ${tone}`}>{icon}</div>
      <p className="summary-label">{label}</p>
      <div className="summary-value">{value}</div>
      <p className="summary-detail">{detail}</p>
    </article>
  )
}

function DataTable({ title, description, headers, rows }) {
  return (
    <section className="panel activity-panel">
      <div className="panel-heading">
        <div><h2>{title}</h2><p>{description}</p></div>
        <span className="muted-tag">{rows.length} records</span>
      </div>
      {rows.length === 0 ? (
        <div className="empty-state"><h3>No records available</h3><p>There is currently no data to display for this section.</p></div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead><tr>{headers.map(h => <th key={h}>{h}</th>)}</tr></thead>
            <tbody>
              {rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{cell ?? '-'}</td>)}</tr>)}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default App
