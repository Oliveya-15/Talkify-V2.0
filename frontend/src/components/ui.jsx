export function StatusBadge({ status }) {
  const styles = {
    completed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    processing: 'bg-amber-50 text-amber-700 border-amber-200',
    uploaded: 'bg-slate-50 text-slate-600 border-slate-200',
    failed: 'bg-red-50 text-red-700 border-red-200',
    unsupported: 'bg-red-50 text-red-700 border-red-200',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${styles[status] || styles.uploaded}`}>
      {status}
    </span>
  );
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6">
      <div className="w-12 h-12 rounded-2xl bg-brand-gradient opacity-90 mb-4 flex items-center justify-center p-2.5 shadow-sm">
        <img src="/white-logo.png" alt="Logo" className="w-full h-full object-contain" />
      </div>
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>
      <p className="text-sm text-slate-500 mt-1 max-w-sm">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Spinner({ className = 'w-4 h-4' }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  );
}

export function Button({ children, variant = 'primary', className = '', ...props }) {
  const base = 'inline-flex items-center justify-center gap-2 rounded-lg text-sm font-medium px-4 py-2.5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed';
  const variants = {
    primary: 'bg-ink text-white hover:bg-slate-800',
    gradient: 'bg-brand-gradient text-white hover:opacity-90',
    secondary: 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50',
    ghost: 'text-slate-600 hover:bg-slate-100',
    danger: 'text-red-600 hover:bg-red-50',
  };
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}

export function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 text-red-700 text-sm px-4 py-3">
      {message}
    </div>
  );
}
