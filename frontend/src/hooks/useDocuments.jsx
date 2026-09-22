import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from './useAuth';

const DocumentsContext = createContext(null);

// "uploaded" is the brief instant right after upload before the background
// task has even started; we treat it the same as "processing" everywhere
// in the UI (see StatusBadge in components/ui.jsx) so the user never sees
// a confusing in-between state.
const ACTIVE_STATUSES = ['uploaded', 'processing'];
const POLL_INTERVAL_MS = 3000;

export function DocumentsProvider({ children }) {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const pollRef = useRef(null);

  const refresh = useCallback(async () => {
    try {
      const docs = await api.listDocuments();
      setDocuments(docs);
      setLoaded(true);
      return docs;
    } catch {
      return [];
    }
  }, []);

  // Load once when a user is authenticated; clear when logged out.
  useEffect(() => {
    if (user) refresh();
    else {
      setDocuments([]);
      setLoaded(false);
    }
  }, [user, refresh]);

  // The actual fix for "I have to reload to see it's processing": as long
  // as at least one document is still uploaded/processing, poll every 3s
  // — from wherever the app happens to be mounted, not just the Documents
  // page — and stop automatically once nothing is left to watch.
  useEffect(() => {
    const hasActive = documents.some((d) => ACTIVE_STATUSES.includes(d.processing_status));
    if (hasActive) {
      pollRef.current = setInterval(refresh, POLL_INTERVAL_MS);
      return () => clearInterval(pollRef.current);
    }
  }, [documents, refresh]);

  // Called right after a successful upload so the new document (status
  // "uploaded") appears instantly, before the first poll even fires.
  const addOptimisticDocument = useCallback((doc) => {
    setDocuments((prev) => [doc, ...prev]);
  }, []);

  const removeDocument = useCallback((id) => {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  }, []);

  const processingCount = documents.filter((d) => ACTIVE_STATUSES.includes(d.processing_status)).length;

  return (
    <DocumentsContext.Provider
      value={{ documents, loaded, refresh, addOptimisticDocument, removeDocument, processingCount }}
    >
      {children}
    </DocumentsContext.Provider>
  );
}

export function useDocuments() {
  const ctx = useContext(DocumentsContext);
  if (!ctx) throw new Error('useDocuments must be used within DocumentsProvider');
  return ctx;
}