import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: DashboardIcon },
  { to: '/documents', label: 'My Documents', icon: DocsIcon },
  { to: '/chat', label: 'Chat', icon: ChatIcon },
  { to: '/history', label: 'History', icon: HistoryIcon },
  { to: '/analytics', label: 'Analytics', icon: AnalyticsIcon },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <aside className="hidden md:flex md:flex-col w-64 shrink-0 border-r border-slate-200 bg-white h-screen sticky top-0">
      <div className="flex items-center gap-2 px-5 h-16 border-b border-slate-200">
        <img src="/talkify-logo.png" alt="Talkify" className="h-8 w-auto" />
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-brand-50 text-brand-700'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-slate-200">
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="w-8 h-8 rounded-full bg-brand-gradient text-white flex items-center justify-center text-xs font-semibold shrink-0">
            {(user?.name || '?').slice(0, 1).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-slate-800 truncate">{user?.name}</p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={() => { logout(); navigate('/login'); }}
          className="mt-1 w-full text-left px-2 py-2 text-sm text-slate-500 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors"
        >
          Log out
        </button>
      </div>
    </aside>
  );
}

function DashboardIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" />
    </svg>
  );
}
function DocsIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M14 3v5h5" /><path d="M9 13h6M9 17h6" />
    </svg>
  );
}
function ChatIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5Z" />
    </svg>
  );
}
function HistoryIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 3" />
    </svg>
  );
}
function AnalyticsIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M3 3v18h18" /><path d="M7 15l4-5 3 3 5-6" />
    </svg>
  );
}
