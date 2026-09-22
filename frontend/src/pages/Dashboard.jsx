import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import AppShell from '../components/AppShell';
import { StatusBadge, EmptyState, Button } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import { useDocuments } from '../hooks/useDocuments';
import { api } from '../services/api';

export default function Dashboard() {
  const { user } = useAuth();
  const { documents, loaded: docsLoaded } = useDocuments(); // live — reflects processing status without a reload
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.analyticsSummary().then(setStats);
  }, []);

  const recentDocs = documents.slice(0, 5);

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <h1 className="text-xl sm:text-2xl font-bold text-ink">Welcome back, {user?.name?.split(' ')[0]}</h1>
        <p className="text-sm sm:text-base text-slate-500 mt-1">Here's what's happening with your documents.</p>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mt-6">
          <StatCard label="Documents" value={stats?.total_documents} loading={!stats} />
          <StatCard label="Processed" value={stats?.completed_documents} loading={!stats} />
          <StatCard label="Conversations" value={stats?.total_conversations} loading={!stats} />
          <StatCard label="Messages sent" value={stats?.total_messages} loading={!stats} />
        </div>

        <div className="mt-8 grid sm:grid-cols-2 gap-3">
          <Link to="/documents" className="rounded-xl border border-slate-200 bg-white p-4 hover:border-brand-300 hover:shadow-sm transition-all">
            <p className="font-semibold text-ink">Upload a document</p>
            <p className="text-sm text-slate-500 mt-0.5">Add a PDF, DOCX, TXT, Markdown, or CSV file.</p>
          </Link>
          <Link to="/chat" className="rounded-xl border border-slate-200 bg-white p-4 hover:border-brand-300 hover:shadow-sm transition-all">
            <p className="font-semibold text-ink">Start a new chat</p>
            <p className="text-sm text-slate-500 mt-0.5">Ask questions about one or more documents.</p>
          </Link>
        </div>

        <div className="mt-8 bg-white border border-slate-200 rounded-xl">
          <div className="px-4 sm:px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-semibold text-ink">Recent documents</h2>
            <Link to="/documents" className="text-sm text-brand-600 hover:underline">View all</Link>
          </div>
          {recentDocs.length === 0 && docsLoaded ? (
            <EmptyState
              title="No documents yet"
              description="Upload your first document to start chatting with it."
              action={<Link to="/documents"><Button variant="gradient">Upload a document</Button></Link>}
            />
          ) : (
            <ul className="divide-y divide-slate-100">
              {recentDocs.map((doc) => (
                <li key={doc.id} className="px-4 sm:px-5 py-3 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-800 truncate">{doc.file_name}</p>
                    <p className="text-xs text-slate-400">{doc.file_type.toUpperCase()} · {(doc.file_size / 1024).toFixed(0)} KB</p>
                  </div>
                  <StatusBadge status={doc.processing_status} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </AppShell>
  );
}

function StatCard({ label, value, loading }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3 sm:p-4">
      <p className="text-xs sm:text-sm text-slate-500">{label}</p>
      <p className="text-xl sm:text-2xl font-bold text-ink mt-1">{loading ? '—' : value ?? 0}</p>
    </div>
  );
}