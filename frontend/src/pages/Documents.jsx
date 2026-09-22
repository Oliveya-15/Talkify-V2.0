import { useRef, useState } from 'react';
import AppShell from '../components/AppShell';
import { StatusBadge, EmptyState, Button, ErrorBanner, Spinner } from '../components/ui';
import { useDocuments } from '../hooks/useDocuments';
import { api } from '../services/api';

const ACCEPTED = ['.pdf', '.docx', '.txt', '.md', '.csv'];

export default function Documents() {
  // Shared with every other page via DocumentsProvider (see App.jsx) — this
  // is what makes a document's status update live everywhere, not just here.
  const { documents, loaded, addOptimisticDocument, removeDocument } = useDocuments();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const uploadFiles = async (files) => {
    setError('');
    setUploading(true);
    try {
      for (const file of files) {
        try {
          const doc = await api.uploadDocument(file); // returns fast — processing happens in the background
          addOptimisticDocument(doc); // shows up immediately with status "uploaded" -> badge reads "processing"
          // No manual polling here anymore — DocumentsProvider notices this
          // document is active and polls automatically until it's done,
          // and that update is visible on this page AND everywhere else.
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
    removeDocument(id);
  };

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-ink">My Documents</h1>
            <p className="text-sm sm:text-base text-slate-500 mt-1">PDF, DOCX, TXT, Markdown, and CSV are supported.</p>
          </div>
          <Button variant="gradient" onClick={() => fileInputRef.current?.click()} disabled={uploading} className="w-full sm:w-auto">
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
          className={`mt-4 rounded-xl border-2 border-dashed p-6 sm:p-8 text-center transition-colors ${
            dragActive ? 'border-brand-400 bg-brand-50' : 'border-slate-200 bg-white'
          }`}
        >
          <p className="text-sm text-slate-500">
            <span className="hidden sm:inline">Drag and drop files here, or </span>
            <button onClick={() => fileInputRef.current?.click()} className="text-brand-600 font-medium hover:underline">
              browse
            </button>
            <span className="hidden sm:inline"> to upload</span>
          </p>
          <p className="text-xs text-slate-400 mt-1">Max 25MB per file · {ACCEPTED.join(', ')}</p>
        </div>

        <div className="mt-6 bg-white border border-slate-200 rounded-xl">
          {!loaded ? (
            <div className="p-8 text-center text-slate-400 text-sm"><Spinner className="w-5 h-5 mx-auto" /></div>
          ) : documents.length === 0 ? (
            <EmptyState title="No documents yet" description="Upload a file above to get started." />
          ) : (
            <ul className="divide-y divide-slate-100">
              {documents.map((doc) => (
                <li key={doc.id} className="px-4 sm:px-5 py-4 flex flex-wrap sm:flex-nowrap items-center justify-between gap-3 sm:gap-4">
                  <div className="min-w-0 flex items-center gap-3 w-full sm:w-auto">
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
                  <div className="flex items-center gap-3 shrink-0 ml-auto sm:ml-0">
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