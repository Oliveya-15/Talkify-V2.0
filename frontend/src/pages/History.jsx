import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import { EmptyState, Spinner } from '../components/ui';
import { api } from '../services/api';

export default function History() {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    api.listConversations().then((c) => { setConversations(c); setLoading(false); });
  }, []);

  const onDelete = async (id, e) => {
    e.stopPropagation();
    if (!confirm('Delete this conversation?')) return;
    await api.deleteConversation(id);
    setConversations((prev) => prev.filter((c) => c.id !== id));
  };

  const filtered = conversations.filter((c) => c.title.toLowerCase().includes(search.toLowerCase()));

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-ink">Chat History</h1>
        <p className="text-slate-500 mt-1">Revisit or continue a previous conversation.</p>

        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search conversations…"
          className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
        />

        <div className="mt-4 bg-white border border-slate-200 rounded-xl">
          {loading ? (
            <div className="p-8 text-center"><Spinner className="w-5 h-5 mx-auto text-slate-400" /></div>
          ) : filtered.length === 0 ? (
            <EmptyState title="No conversations found" description="Start a new chat to see it appear here." />
          ) : (
            <ul className="divide-y divide-slate-100">
              {filtered.map((c) => (
                <li
                  key={c.id}
                  onClick={() => navigate('/chat')}
                  className="px-5 py-4 flex items-center justify-between cursor-pointer hover:bg-slate-50 transition-colors"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-800 truncate">{c.title}</p>
                    <p className="text-xs text-slate-400">
                      {c.document_ids.length} document(s) · updated {new Date(c.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                  <button onClick={(e) => onDelete(c.id, e)} className="text-xs text-slate-400 hover:text-red-600 shrink-0">
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </AppShell>
  );
}
