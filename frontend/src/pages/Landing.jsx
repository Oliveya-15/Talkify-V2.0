import { Link } from 'react-router-dom';

const FEATURES = [
  {
    title: 'Grounded, cited answers',
    desc: 'Every answer is backed by real excerpts from your documents, with clickable citations pointing to the exact page.',
  },
  {
    title: 'Hybrid search',
    desc: 'Combines semantic (embedding-based) search with keyword search, so both "meaning" and exact-term questions work well.',
  },
  {
    title: 'Multi-document chat',
    desc: 'Scope a conversation to one document or several, and ask questions across all of them at once.',
  },
  {
    title: 'Multi-format ingestion',
    desc: 'PDF, DOCX, TXT, Markdown, and CSV are all supported out of the box.',
  },
  {
    title: 'Private by design',
    desc: "Every document and conversation is scoped to your account. Nobody else's data ever appears in your results.",
  },
  {
    title: 'Free-first pipeline',
    desc: 'Runs on free, local, open-source embeddings and search — an LLM API key is optional, not required.',
  },
];

const STEPS = [
  { n: '1', title: 'Upload', desc: 'Add PDFs, DOCX, TXT, Markdown, or CSV files to your library.' },
  { n: '2', title: 'Process', desc: 'Talkify extracts, chunks, and indexes the text for semantic + keyword search.' },
  { n: '3', title: 'Ask', desc: 'Chat with one document or many — every answer comes with real citations.' },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      <header className="max-w-6xl mx-auto flex items-center justify-between px-4 sm:px-6 py-4 sm:py-5">
        <img src="/talkify-logo.png" alt="Talkify" className="h-7 sm:h-9 w-auto" />
        <nav className="flex items-center gap-1.5 sm:gap-3">
          <Link to="/login" className="text-xs sm:text-sm font-medium text-slate-600 hover:text-slate-900 px-2.5 sm:px-3 py-2">
            Log in
          </Link>
          <Link to="/register" className="text-xs sm:text-sm font-medium text-white bg-ink hover:bg-slate-800 rounded-lg px-3 sm:px-4 py-2 transition-colors">
            Get started
          </Link>
        </nav>
      </header>

      <section className="max-w-4xl mx-auto text-center px-6 pt-16 pb-20">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-ink leading-tight">
          Understand your documents.
          <br />
          <span className="bg-brand-gradient bg-clip-text text-transparent">Ask better questions.</span>
        </h1>
        <p className="mt-5 text-lg text-slate-600 max-w-2xl mx-auto">
          Talkify is an AI document intelligence assistant. Upload your files and get
          grounded, citation-backed answers — not guesses.
        </p>
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3 px-4">
          <Link to="/register" className="w-full sm:w-auto text-center rounded-lg bg-brand-gradient text-white font-medium px-6 py-3 hover:opacity-90 transition-opacity">
            Start for free
          </Link>
          <Link to="/login" className="w-full sm:w-auto text-center rounded-lg border border-slate-200 text-slate-700 font-medium px-6 py-3 hover:bg-slate-50 transition-colors">
            I already have an account
          </Link>
        </div>
      </section>

      <section className="bg-slate-50 border-y border-slate-100 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-brand-600 text-center">How it works</h2>
          <div className="mt-8 grid sm:grid-cols-3 gap-8">
            {STEPS.map((s) => (
              <div key={s.n} className="text-center">
                <div className="w-10 h-10 mx-auto rounded-full bg-brand-gradient text-white flex items-center justify-center font-semibold">
                  {s.n}
                </div>
                <h3 className="mt-3 font-semibold text-ink">{s.title}</h3>
                <p className="mt-1 text-sm text-slate-500">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-20">
        <h2 className="text-2xl font-bold text-ink text-center">What Talkify does</h2>
        <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-xl border border-slate-200 p-5 hover:border-brand-200 transition-colors">
              <h3 className="font-semibold text-ink">{f.title}</h3>
              <p className="mt-1.5 text-sm text-slate-500">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-6 pb-20">
        <div className="rounded-2xl bg-ink text-white px-8 py-10 text-center">
          <h2 className="text-2xl font-bold">Built with a transparent, hand-implemented RAG pipeline</h2>
          <p className="mt-2 text-slate-300 max-w-xl mx-auto">
            Chunking, embeddings, hybrid retrieval, and citation mapping are implemented as
            understandable Python modules — not hidden behind a single framework call.
          </p>
        </div>
      </section>

      <footer className="border-t border-slate-100 py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <img src="/talkify-logo.png" alt="Talkify" className="h-5 w-auto opacity-70" />
          <p className="text-xs text-slate-400">Built as a student portfolio project. Not for professional/legal/medical advice.</p>
        </div>
      </footer>
    </div>
  );
}