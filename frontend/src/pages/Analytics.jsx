import { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import { Spinner } from '../components/ui';
import { api } from '../services/api';

export default function Analytics() {
  const [stats, setStats] = useState(null);

  useEffect(() => { api.analyticsSummary().then(setStats); }, []);

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-ink">Analytics</h1>
        <p className="text-slate-500 mt-1">Real usage numbers from your account — nothing here is estimated.</p>

        {!stats ? (
          <div className="mt-8"><Spinner className="w-5 h-5 text-slate-400" /></div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
            <Card label="Total documents" value={stats.total_documents} />
            <Card label="Successfully processed" value={stats.completed_documents} />
            <Card label="Failed to process" value={stats.failed_documents} />
            <Card label="Conversations" value={stats.total_conversations} />
            <Card label="Messages exchanged" value={stats.total_messages} />
          </div>
        )}

        <div className="mt-10 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6">
          <h2 className="font-semibold text-ink">Retrieval evaluation (developer metrics)</h2>
          <p className="text-sm text-slate-500 mt-1">
            Precision@k, recall@k, and citation-accuracy numbers are computed by
            <code className="mx-1 px-1.5 py-0.5 bg-white border border-slate-200 rounded text-xs">
              backend/evaluation/retrieval_metrics.py
            </code>
            against a manually verified question set. They're kept out of this in-app
            page deliberately — the spec calls for separating private developer
            evaluation from user-facing analytics — and are reported instead in the
            project's README/evaluation docs.
          </p>
        </div>
      </div>
    </AppShell>
  );
}

function Card({ label, value }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-3xl font-bold text-ink mt-1">{value}</p>
    </div>
  );
}
