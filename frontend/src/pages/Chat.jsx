import { useEffect, useRef, useState } from 'react';
import AppShell from '../components/AppShell';
import ChatMessage from '../components/ChatMessage';
import { Button, EmptyState, ErrorBanner, Spinner } from '../components/ui';
import { useDocuments } from '../hooks/useDocuments';
import { api } from '../services/api';

const SUGGESTED_QUESTIONS = [
  'What are the main points of this document?',
  'Summarize this in a few sentences.',
  'What key facts or numbers does it mention?',
];

export default function Chat() {
  // Shared, live-updating list from DocumentsProvider — if a document
  // finishes processing while you're already on this page (or you upload
  // one from another tab of the app), it becomes selectable automatically.
  const { documents, loaded: docsLoaded } = useDocuments();
  const docs = documents.filter((d) => d.processing_status === 'completed');

  const [conversations, setConversations] = useState([]);
  const [activeConvo, setActiveConvo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState('');
  const [loadingConvos, setLoadingConvos] = useState(true);
  const [convoPanelOpen, setConvoPanelOpen] = useState(false); // mobile/tablet drawer
  const scrollRef = useRef(null);

  useEffect(() => {
    api.listConversations().then((convos) => {
      setConversations(convos);
      setLoadingConvos(false);
    });
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const openConversation = async (convo) => {
    setActiveConvo(convo);
    setSelectedDocIds(convo.document_ids);
    setMessages(await api.getMessages(convo.id));
    setConvoPanelOpen(false); // close the mobile drawer once a conversation is picked
  };

  const ensureConversation = async () => {
    if (activeConvo) return activeConvo.id;
    if (selectedDocIds.length === 0) {
      throw new Error('Select at least one document to chat with.');
    }
    const convo = await api.createConversation({ document_ids: selectedDocIds });
    setConversations((prev) => [convo, ...prev]);
    setActiveConvo(convo);
    return convo.id;
  };

  const ask = async (text) => {
    const q = (text ?? question).trim();
    if (!q) return;
    setError('');

    let convoId;
    try {
      convoId = await ensureConversation();
    } catch (err) {
      setError(err.message);
      return;
    }

    setQuestion('');
    setMessages((prev) => [...prev, { id: `temp-${Date.now()}`, role: 'user', content: q, citations: [] }]);
    setAsking(true);
    try {
      const answer = await api.ask(convoId, q);
      setMessages((prev) => [...prev, answer]);
    } catch (err) {
      setError(err.message);
    } finally {
      setAsking(false);
    }
  };

  const giveFeedback = (messageId, rating) => {
    if (messageId.startsWith('temp-')) return;
    api.giveFeedback(messageId, { rating }).catch(() => {});
  };

  const startNew = () => {
    setActiveConvo(null);
    setMessages([]);
    setSelectedDocIds([]);
    setError('');
    setConvoPanelOpen(false);
  };

  return (
    <AppShell>
      <div className="flex h-full relative">
        {/* Backdrop for the conversation list drawer — tablet/mobile only */}
        {convoPanelOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/30 lg:hidden"
            onClick={() => setConvoPanelOpen(false)}
            aria-hidden="true"
          />
        )}

        {/* Conversation list: a static column on large screens, a slide-in
            drawer below that (see the mobile toggle button further down). */}
        <div
          className={`
            fixed inset-y-0 left-0 z-50 w-72 border-r border-slate-200 bg-white shrink-0 flex flex-col
            transform transition-transform duration-200 ease-in-out
            ${convoPanelOpen ? 'translate-x-0' : '-translate-x-full'}
            lg:static lg:z-auto lg:translate-x-0 lg:flex
          `}
        >
          <div className="p-4 border-b border-slate-100 flex items-center gap-2">
            <Button variant="secondary" className="w-full" onClick={startNew}>
              + New conversation
            </Button>
            <button
              onClick={() => setConvoPanelOpen(false)}
              aria-label="Close conversations"
              className="lg:hidden text-slate-400 hover:text-slate-600 p-1.5 shrink-0"
            >
              <CloseIcon className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin">
            {loadingConvos ? (
              <div className="p-4 text-center text-slate-400 text-sm"><Spinner className="w-4 h-4 mx-auto" /></div>
            ) : conversations.length === 0 ? (
              <p className="p-4 text-sm text-slate-400">No conversations yet.</p>
            ) : (
              conversations.map((c) => (
                <button
                  key={c.id}
                  onClick={() => openConversation(c)}
                  className={`w-full text-left px-4 py-3 border-b border-slate-50 hover:bg-slate-50 transition-colors ${
                    activeConvo?.id === c.id ? 'bg-brand-50' : ''
                  }`}
                >
                  <p className="text-sm font-medium text-slate-800 truncate">{c.title}</p>
                  <p className="text-xs text-slate-400">{c.document_ids.length} document(s)</p>
                </button>
              ))
            )}
          </div>
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          {/* Mobile/tablet-only bar: this is the only way to reach the
              conversation list below the lg breakpoint, since it's hidden
              as a static column there. */}
          <div className="lg:hidden flex items-center justify-between px-4 h-12 border-b border-slate-200 bg-white shrink-0">
            <button
              onClick={() => setConvoPanelOpen(true)}
              className="flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900"
            >
              <ListIcon className="w-4 h-4" /> Conversations
            </button>
            {activeConvo && <span className="text-xs text-slate-400 truncate max-w-[45%]">{activeConvo.title}</span>}
          </div>

          {!activeConvo && (
            <div className="p-4 border-b border-slate-100 bg-white shrink-0">
              <p className="text-sm font-medium text-slate-700 mb-2">Select document(s) to chat with:</p>
              <div className="flex flex-wrap gap-2">
                {!docsLoaded ? (
                  <Spinner className="w-4 h-4 text-slate-400" />
                ) : docs.length === 0 ? (
                  <p className="text-sm text-slate-400">No processed documents yet — upload one first.</p>
                ) : (
                  docs.map((d) => {
                    const selected = selectedDocIds.includes(d.id);
                    return (
                      <button
                        key={d.id}
                        onClick={() =>
                          setSelectedDocIds((prev) =>
                            selected ? prev.filter((id) => id !== d.id) : [...prev, d.id]
                          )
                        }
                        className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                          selected ? 'bg-brand-600 text-white border-brand-600' : 'bg-white text-slate-600 border-slate-200 hover:border-brand-300'
                        }`}
                      >
                        {d.file_name}
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          )}

          <div ref={scrollRef} className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-6 space-y-4">
            {messages.length === 0 ? (
              <EmptyState
                title="Ask anything about your documents"
                description="Select one or more documents, then ask a question. Every answer includes citations back to the source."
              />
            ) : (
              messages.map((m) => <ChatMessage key={m.id} message={m} onFeedback={giveFeedback} />)
            )}
            {asking && (
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 text-sm text-slate-400 flex items-center gap-2">
                  <Spinner className="w-4 h-4" /> Thinking…
                </div>
              </div>
            )}
          </div>

          {messages.length === 0 && !activeConvo && docs.length > 0 && (
            <div className="px-4 sm:px-6 pb-2 flex flex-wrap gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => setQuestion(q)}
                  className="text-xs bg-white border border-slate-200 rounded-full px-3 py-1.5 text-slate-600 hover:border-brand-300"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          <div className="p-3 sm:p-4 border-t border-slate-200 bg-white shrink-0">
            <ErrorBanner message={error} />
            <form onSubmit={(e) => { e.preventDefault(); ask(); }} className="mt-2 flex items-end gap-2">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); } }}
                rows={1}
                placeholder="Ask a question — e.g. 'in 50 words' or 'as bullet points'…"
                className="flex-1 resize-none rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
              />
              <Button type="submit" variant="gradient" disabled={asking || !question.trim()}>
                Send
              </Button>
            </form>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function CloseIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M18 6 6 18M6 6l12 12" />
    </svg>
  );
}

function ListIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M4 6h16M4 12h16M4 18h10" />
    </svg>
  );
}