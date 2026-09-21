import { useCallback, useEffect, useRef, useState } from 'react';
import AppShell from '../components/AppShell';
import { StatusBadge, EmptyState, Button, ErrorBanner, Spinner } from '../components/ui';
import { api } from '../services/api';

const ACCEPTED = ['.pdf', '.docx', '.txt', '.md', '.csv'];

export default function Documents() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setDocs(await api.listDocuments());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const pollUntilDone = async (id) => {
    const terminal = ['completed', 'failed', 'unsupported'];
    for (let attempt = 0; attempt < 60; attempt++) {
      await new Promise((r) => setTimeout(r, 1200));
      let doc;
      try {
        doc = await api.getDocument(id);
      } catch {
        return; // document was deleted mid-poll
      }
      setDocs((prev) => prev.map((d) => (d.id === id ? doc : d)));
      if (terminal.includes(doc.processing_status)) return;
    }
  };

  const uploadFiles = async (files) => {
    setError('');
    setUploading(true);
    try {
      for (const file of files) {
        try {
          const doc = await api.uploadDocument(file); // returns fast now — processing happens in the background
          setDocs((prev) => [doc, ...prev]);
          pollUntilDone(doc.id); // fire-and-forget; updates this doc's row as it progresses
        } catch (err) {
          setError(`"${file.name}": ${err.message}`);
        }
      }
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files?.length) uploadFiles(Array.from(e.dataTransfer.files));
  };

  const onDelete = async (id) => {
    if (!confirm('Delete this document? This also removes its chat history context.')) return;
    await api.deleteDocument(id);
    refresh();
  };

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-ink">My Documents</h1>
            <p className="text-slate-500 mt-1">PDF, DOCX, TXT, Markdown, and CSV are supported.</p>
          </div>
          <Button variant="gradient" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            {uploading ? <><Spinner /> Uploading…</> : 'Upload document'}
          </Button>
          <input
            ref={fileInputRef} type="file" multiple hidden accept={ACCEPTED.join(',')}
            onChange={(e) => e.target.files?.length && uploadFiles(Array.from(e.target.files))}
          />
        </div>

        <div className="mt-4"><ErrorBanner message={error} /></div>

        <div
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={onDrop}
          className={`mt-4 rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
            dragActive ? 'border-brand-400 bg-brand-50' : 'border-slate-200 bg-white'
          }`}
        >
          <p className="text-sm text-slate-500">
            Drag and drop files here, or{' '}
            <button onClick={() => fileInputRef.current?.click()} className="text-brand-600 font-medium hover:underline">
              browse
            </button>
          </p>
          <p className="text-xs text-slate-400 mt-1">Max 25MB per file · {ACCEPTED.join(', ')}</p>
        </div>

        <div className="mt-6 bg-white border border-slate-200 rounded-xl">
          {loading ? (
            <div className="p-8 text-center text-slate-400 text-sm"><Spinner className="w-5 h-5 mx-auto" /></div>
          ) : docs.length === 0 ? (
            <EmptyState title="No documents yet" description="Upload a file above to get started." />
          ) : (
            <ul className="divide-y divide-slate-100">
              {docs.map((doc) => (
                <li key={doc.id} className="px-5 py-4 flex items-center justify-between gap-4">
                  <div className="min-w-0 flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center text-xs font-bold uppercase shrink-0">
                      {doc.file_type}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-800 truncate">{doc.file_name}</p>
                      <p className="text-xs text-slate-400">
                        {(doc.file_size / 1024).toFixed(0)} KB
                        {doc.page_count ? ` · ${doc.page_count} page${doc.page_count > 1 ? 's' : ''}` : ''}
                        {doc.processing_error ? ` · ${doc.processing_error}` : ''}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <StatusBadge status={doc.processing_status} />
                    <button onClick={() => onDelete(doc.id)} className="text-xs text-slate-400 hover:text-red-600">
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </AppShell>
  );
}
