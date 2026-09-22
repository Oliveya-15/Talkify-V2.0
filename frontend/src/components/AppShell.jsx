import { useState } from 'react';
import Sidebar from './Sidebar';
import { Spinner } from './ui';
import { useDocuments } from '../hooks/useDocuments';

export default function AppShell({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 min-w-0 flex flex-col h-screen">
        {/* Mobile-only top bar — this is the app's only way to open navigation
            on small screens, since the sidebar itself is hidden by default there. */}
        <header className="md:hidden flex items-center justify-between px-4 h-14 border-b border-slate-200 bg-white shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
            className="p-1.5 -ml-1.5 text-slate-600 hover:text-slate-900"
          >
            <MenuIcon className="w-6 h-6" />
          </button>
          <img src="/talkify-logo.png" alt="Talkify" className="h-6 w-auto" />
          <div className="w-8" /> {/* balances the menu button so the logo stays centered */}
        </header>

        <ProcessingBanner />

        <main className="flex-1 min-h-0 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}

function ProcessingBanner() {
  const { processingCount } = useDocuments();
  if (!processingCount) return null;
  return (
    <div className="shrink-0 flex items-center gap-2 bg-amber-50 border-b border-amber-200 text-amber-800 text-xs sm:text-sm px-4 py-2">
      <Spinner className="w-3.5 h-3.5 shrink-0" />
      <span>
        Processing {processingCount} document{processingCount > 1 ? 's' : ''}… feel free to keep
        browsing, this finishes in the background.
      </span>
    </div>
  );
}

function MenuIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M4 7h16M4 12h16M4 17h16" />
    </svg>
  );
}