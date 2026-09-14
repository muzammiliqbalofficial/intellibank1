import { useState, useEffect } from 'react';
import axios from 'axios';

const API = 'http://localhost:8000/api';

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: '' },
  { id: 'fraud', label: 'Fraud Monitor', icon: '' },
  { id: 'churn', label: 'Churn Analysis', icon: '' },
  { id: 'upload', label: 'Data Upload', icon: '' },
];

export default function App() {
  const [auth, setAuth] = useState(null);
  const [tab, setTab] = useState('dashboard');
  if (!auth) return <Login setAuth={setAuth} />;
  return (
    <div style={{ display: 'flex', height: '100vh', background: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
      <Sidebar auth={auth} tab={tab} setTab={setTab} setAuth={setAuth} />
      <main style={{ flex: 1, overflowY: 'auto', padding: '40px' }}>
        {tab === 'dashboard' && <Dashboard />}
        {tab === 'fraud' && <FraudPage />}
        {tab === 'churn' && <ChurnPage />}
        {tab === 'upload' && <UploadPage />}
      </main>
    </div>
  );
}

function Sidebar({ auth, tab, setTab, setAuth }) {
  return (
    <aside style={{ width: 260, background: '#1e293b', display: 'flex', flexDirection: 'column', boxShadow: '4px 0 20px rgba(0,0,0,0.15)' }}>
      <div style={{ padding: '32px 24px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 42, height: 42, background: 'linear-gradient(135deg,#3b82f6,#1d4ed8)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22 }}></div>
          <div>
            <div style={{ color: '#fff', fontWeight: 800, fontSize: 18, letterSpacing: -0.5 }}>IntelliBank</div>
            <div style={{ color: '#64748b', fontSize: 11, letterSpacing: 2, textTransform: 'uppercase', marginTop: 2 }}>AI Analytics</div>
          </div>
        </div>
      </div>
      <nav style={{ flex: 1, padding: '16px 12px' }}>
        {NAV.map(n => (
          <button key={n.id} onClick={() => setTab(n.id)} style={{
            display: 'flex', alignItems: 'center', gap: 12, width: '100%', padding: '12px 14px',
            borderRadius: 10, marginBottom: 4, border: 'none', cursor: 'pointer', textAlign: 'left', fontSize: 14, fontWeight: 600,
            background: tab === n.id ? 'linear-gradient(135deg,rgba(59,130,246,0.25),rgba(29,78,216,0.15))' : 'transparent',
            color: tab === n.id ? '#60a5fa' : '#94a3b8',
            transition: 'all 0.2s',
          }}>
            <span style={{ fontSize: 18 }}>{n.icon}</span> {n.label}
          </button>
        ))}
      </nav>
      <div style={{ padding: '20px 24px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ color: '#fff', fontWeight: 600, fontSize: 14 }}>{auth.username}</div>
        <div style={{ color: '#3b82f6', fontSize: 12, marginBottom: 12 }}>{auth.role}</div>
        <button onClick={() => setAuth(null)} style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#f87171', padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13, width: '100%', fontWeight: 600 }}>
          Logout
        </button>
      </div>
    </aside>
  );
}

function Login({ setAuth }) {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [err, setErr] = useState('');
  const submit = async (e) => {
    e.preventDefault();
    try {
      const r = await axios.post(`${API}/login`, { username: user, password: pass });
      if (r.data.success) setAuth(r.data);
    } catch { setErr('Invalid credentials. Please try again.'); }
  };
  return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg,#f0f4ff 0%,#e8f4fd 100%)', fontFamily: 'Inter, sans-serif' }}>
      <div style={{ background: '#fff', padding: 48, borderRadius: 24, boxShadow: '0 20px 60px rgba(0,0,0,0.08)', width: 420, border: '1px solid #e2e8f0' }}>
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{ width: 72, height: 72, background: 'linear-gradient(135deg,#3b82f6,#1d4ed8)', borderRadius: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 36, margin: '0 auto 16px', boxShadow: '0 8px 24px rgba(59,130,246,0.35)' }}></div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', margin: 0 }}>IntelliBank AI</h1>
          <p style={{ color: '#64748b', fontSize: 14, marginTop: 6 }}>Secure Access Portal</p>
        </div>
        {err && <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '12px 16px', borderRadius: 10, marginBottom: 20, fontSize: 14 }}>{err}</div>}
        <form onSubmit={submit}>
          <div style={{ marginBottom: 18 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 8 }}>Username</label>
            <input value={user} onChange={e => setUser(e.target.value)} placeholder="admin" required
              style={{ width: '100%', padding: '12px 16px', border: '1.5px solid #e2e8f0', borderRadius: 10, fontSize: 14, color: '#0f172a', outline: 'none', boxSizing: 'border-box', background: '#f8fafc' }} />
          </div>
          <div style={{ marginBottom: 28 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 8 }}>Password</label>
            <input type="password" value={pass} onChange={e => setPass(e.target.value)} placeholder="••••••••" required
              style={{ width: '100%', padding: '12px 16px', border: '1.5px solid #e2e8f0', borderRadius: 10, fontSize: 14, color: '#0f172a', outline: 'none', boxSizing: 'border-box', background: '#f8fafc' }} />
          </div>
          <button type="submit" style={{ width: '100%', padding: '14px', background: 'linear-gradient(135deg,#3b82f6,#1d4ed8)', color: '#fff', border: 'none', borderRadius: 12, fontSize: 15, fontWeight: 700, cursor: 'pointer', boxShadow: '0 8px 20px rgba(59,130,246,0.35)' }}>
            Sign In
          </button>
        </form>
        <div style={{ marginTop: 24, padding: 16, background: '#f8fafc', borderRadius: 10, border: '1px solid #e2e8f0', fontSize: 13, color: '#64748b' }}>
          <b>Admin:</b> admin / admin123 &nbsp;|&nbsp; <b>Manager:</b> manager / manager123
        </div>
      </div>
    </div>
  );
}

function Card({ children, style = {} }) {
  return <div style={{ background: '#fff', borderRadius: 16, padding: 28, boxShadow: '0 2px 12px rgba(0,0,0,0.06)', border: '1px solid #e2e8f0', ...style }}>{children}</div>;
}

function KPI({ label, value, icon, color = '#3b82f6' }) {
  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: '#64748b', letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 8 }}>{label}</div>
          <div style={{ fontSize: 40, fontWeight: 900, color: '#0f172a', lineHeight: 1 }}>{value}</div>
        </div>
        <div style={{ width: 52, height: 52, background: color + '18', borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26 }}>{icon}</div>
      </div>
    </Card>
  );
}

function PageHeader({ title, subtitle, color = '#3b82f6' }) {
  return (
    <div style={{ marginBottom: 32 }}>
      <h2 style={{ fontSize: 32, fontWeight: 900, color: '#0f172a', margin: 0, letterSpacing: -1 }}>{title}</h2>
      <p style={{ color: '#64748b', fontSize: 15, marginTop: 6 }}>{subtitle}</p>
    </div>
  );
}

function EmptyState({ message }) {
  return (
    <div style={{ textAlign: 'center', padding: '60px 20px', color: '#94a3b8' }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}></div>
      <div style={{ fontSize: 15, fontWeight: 600 }}>{message}</div>
      <div style={{ fontSize: 13, marginTop: 8 }}>Upload data via the Data Upload tab to populate analytics.</div>
    </div>
  );
}

function Dashboard() {
  const [stats, setStats] = useState(null);
  useEffect(() => { axios.get(`${API}/stats`).then(r => setStats(r.data)).catch(() => setStats({ customers: 0, branches: 6, transactions: 0 })); }, []);

  if (!stats) return <div style={{ color: '#64748b', padding: 40 }}>Loading...</div>;
  return (
    <div>
      <PageHeader title="Executive Dashboard" subtitle="High-level overview of banking operations and AI system status." />
      {stats.transactions === 0 && (
        <div style={{ background: '#fffbeb', border: '1px solid #fbbf24', borderRadius: 12, padding: '16px 20px', marginBottom: 28, display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 20 }}></span>
          <div>
            <b style={{ color: '#92400e' }}>No Data Loaded</b>
            <p style={{ color: '#78350f', fontSize: 13, margin: '4px 0 0' }}>Upload CSV files in the <b>Data Upload</b> tab to activate analytics and AI models.</p>
          </div>
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 28 }}>
        <KPI label="Total Customers" value={stats.customers.toLocaleString()} icon="" color="#3b82f6" />
        <KPI label="Transactions" value={stats.transactions.toLocaleString()} icon="" color="#8b5cf6" />
        <KPI label="Branches" value={stats.branches} icon="" color="#10b981" />
      </div>
      <Card>
        <h3 style={{ margin: '0 0 12px', color: '#1e293b', fontWeight: 700 }}>About IntelliBank AI</h3>
        <p style={{ color: '#64748b', fontSize: 14, lineHeight: 1.7, margin: 0 }}>
          This system dynamically ingests CSV banking data and applies trained machine learning models (XGBoost for fraud, Random Forest for churn) to generate real-time analytics. All metrics update automatically after data is uploaded.
        </p>
      </Card>
    </div>
  );
}

function DataTable({ columns, rows, emptyMsg }) {
  if (!rows || rows.length === 0) return <EmptyState message={emptyMsg} />;
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
        <thead>
          <tr style={{ background: '#f8fafc' }}>
            {columns.map(c => <th key={c.key} style={{ padding: '12px 16px', textAlign: c.align || 'left', color: '#64748b', fontWeight: 700, fontSize: 12, letterSpacing: 1, textTransform: 'uppercase', borderBottom: '2px solid #e2e8f0' }}>{c.label}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #f1f5f9', background: i % 2 === 0 ? '#fff' : '#f8fafc' }}>
              {columns.map(c => <td key={c.key} style={{ padding: '12px 16px', color: '#1e293b', textAlign: c.align || 'left' }}>{c.render ? c.render(row[c.key], row) : row[c.key]}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Badge({ value, type = 'red' }) {
  const colors = { red: { bg: '#fef2f2', color: '#dc2626', border: '#fecaca' }, orange: { bg: '#fff7ed', color: '#c2410c', border: '#fed7aa' }, green: { bg: '#f0fdf4', color: '#16a34a', border: '#bbf7d0' } };
  const c = colors[type];
  return <span style={{ background: c.bg, color: c.color, border: `1px solid ${c.border}`, padding: '4px 10px', borderRadius: 6, fontWeight: 700, fontSize: 13 }}>{value}</span>;
}

function FraudPage() {
  const [data, setData] = useState(null);
  useEffect(() => { axios.get(`${API}/fraud`).then(r => setData(r.data)).catch(() => setData({ data: [], stats: { total: 0, alerts: 0 } })); }, []);
  if (!data) return <div style={{ padding: 40, color: '#64748b' }}>Running AI inference...</div>;
  const rows = data.data.filter(r => r.risk_score > 70).slice(0, 15);
  return (
    <div>
      <PageHeader title="Fraud Monitor" subtitle="XGBoost-powered real-time transaction anomaly detection." />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 28 }}>
        <KPI label="Transactions Screened" value={data.stats.total.toLocaleString()} icon="" color="#3b82f6" />
        <KPI label="Critical Alerts" value={data.stats.alerts} icon="" color="#ef4444" />
      </div>
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h3 style={{ margin: 0, color: '#0f172a', fontWeight: 800 }}>High-Risk Transactions</h3>
          <Badge value="Live Monitor" type="red" />
        </div>
        <DataTable
          columns={[
            { key: 'trans_id', label: 'Transaction ID', render: v => <span style={{ fontFamily: 'monospace', color: '#3b82f6' }}>#{v}</span> },
            { key: 'branch_name', label: 'Branch' },
            { key: 'category', label: 'Category' },
            { key: 'amount', label: 'Amount', render: v => <b style={{ color: '#059669' }}>${Number(v).toFixed(2)}</b> },
            { key: 'risk_score', label: 'Risk Score', align: 'right', render: v => <Badge value={`${Number(v).toFixed(1)}%`} type="red" /> },
          ]}
          rows={rows}
          emptyMsg="No high-risk transactions detected. Upload transaction data to begin screening."
        />
      </Card>
    </div>
  );
}

function ChurnPage() {
  const [data, setData] = useState(null);
  useEffect(() => { axios.get(`${API}/churn`).then(r => setData(r.data)).catch(() => setData({ data: [], stats: { high_risk: 0 } })); }, []);
  if (!data) return <div style={{ padding: 40, color: '#64748b' }}>Running AI inference...</div>;
  const rows = data.data.filter(r => r.churn_risk > 60).slice(0, 15);
  return (
    <div>
      <PageHeader title="Churn Analysis" subtitle="Random Forest model predicting customer retention risk scores." />
      <div style={{ marginBottom: 28 }}>
        <KPI label="High-Risk Customers" value={data.stats.high_risk} icon="" color="#f59e0b" />
      </div>
      <Card>
        <h3 style={{ margin: '0 0 20px', color: '#0f172a', fontWeight: 800 }}>At-Risk Customer Registry</h3>
        <DataTable
          columns={[
            { key: 'name', label: 'Customer Name', render: v => <b style={{ color: '#0f172a' }}>{v}</b> },
            { key: 'age', label: 'Age', render: v => `${v} yrs` },
            { key: 'tenure', label: 'Tenure', render: v => `${v} yrs` },
            { key: 'balance', label: 'Balance', render: v => <span style={{ color: '#059669', fontWeight: 700 }}>${Number(v).toFixed(2)}</span> },
            { key: 'churn_risk', label: 'Flight Risk', align: 'right', render: v => <Badge value={`${Number(v).toFixed(1)}%`} type="orange" /> },
          ]}
          rows={rows}
          emptyMsg="No high-risk customers detected. Upload customer data to begin churn analysis."
        />
      </Card>
    </div>
  );
}

function UploadPage() {
  const [file, setFile] = useState(null);
  const [table, setTable] = useState('Transactions');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);
  const upload = async () => {
    if (!file) return;
    setLoading(true); setMsg(null);
    const fd = new FormData(); fd.append('file', file);
    try {
      const r = await axios.post(`${API}/upload?table=${table}`, fd);
      setMsg({ type: 'success', text: ` ${r.data.message}` });
      setFile(null);
    } catch (e) {
      setMsg({ type: 'error', text: ` Upload failed: ${e.response?.data?.detail || 'Unknown error'}` });
    }
    setLoading(false);
  };
  return (
    <div style={{ maxWidth: 640 }}>
      <PageHeader title="Data Upload" subtitle="Ingest CSV datasets to power the AI analytics engine." />
      <Card>
        {msg && <div style={{ padding: '14px 18px', borderRadius: 10, marginBottom: 24, fontSize: 14, fontWeight: 600, background: msg.type === 'success' ? '#f0fdf4' : '#fef2f2', color: msg.type === 'success' ? '#16a34a' : '#dc2626', border: `1px solid ${msg.type === 'success' ? '#bbf7d0' : '#fecaca'}` }}>{msg.text}</div>}
        
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', fontWeight: 700, fontSize: 13, color: '#374151', marginBottom: 8 }}>Target Table</label>
          <select value={table} onChange={e => setTable(e.target.value)} style={{ width: '100%', padding: '12px 16px', border: '1.5px solid #e2e8f0', borderRadius: 10, fontSize: 14, color: '#0f172a', background: '#f8fafc', outline: 'none' }}>
            <option value="Transactions">Transactions - feeds Fraud Detection AI</option>
            <option value="Customers">Customers - feeds Churn Analysis AI</option>
          </select>
        </div>

        <div style={{ marginBottom: 28 }}>
          <label style={{ display: 'block', fontWeight: 700, fontSize: 13, color: '#374151', marginBottom: 8 }}>Select CSV File</label>
          <div style={{ border: '2px dashed #cbd5e1', borderRadius: 12, padding: 32, textAlign: 'center', background: '#f8fafc', cursor: 'pointer' }}>
            <div style={{ fontSize: 36, marginBottom: 10 }}></div>
            <input type="file" accept=".csv" onChange={e => setFile(e.target.files[0])} style={{ fontSize: 14, color: '#64748b' }} />
            {file && <div style={{ marginTop: 12, color: '#3b82f6', fontWeight: 600, fontSize: 14 }}>Selected: {file.name}</div>}
          </div>
        </div>

        <button onClick={upload} disabled={!file || loading} style={{ width: '100%', padding: 16, background: file && !loading ? 'linear-gradient(135deg,#3b82f6,#1d4ed8)' : '#e2e8f0', color: file && !loading ? '#fff' : '#94a3b8', border: 'none', borderRadius: 12, fontSize: 15, fontWeight: 700, cursor: file && !loading ? 'pointer' : 'not-allowed', boxShadow: file && !loading ? '0 8px 20px rgba(59,130,246,0.3)' : 'none', transition: 'all 0.2s' }}>
          {loading ? 'Uploading...' : 'Upload & Process Data'}
        </button>

        <div style={{ marginTop: 24, padding: 16, background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 10 }}>
          <b style={{ color: '#0369a1', fontSize: 13 }}> How it works:</b>
          <ul style={{ margin: '8px 0 0', paddingLeft: 20, color: '#0369a1', fontSize: 13, lineHeight: 1.8 }}>
            <li>Upload your <b>Transaction CSV</b> to enable Fraud Detection analytics</li>
            <li>Upload your <b>Customer CSV</b> to enable Churn Prediction analytics</li>
            <li>All charts and KPIs update automatically after upload</li>
          </ul>
        </div>
      </Card>
    </div>
  );
}
