import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Button, ErrorBanner, Spinner } from '../components/ui';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to continue to your documents.">
      <form onSubmit={onSubmit} className="space-y-4">
        <ErrorBanner message={error} />
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
          <input
            type="email" required autoComplete="email" value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent"
            placeholder="you@example.com"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
          <input
            type="password" required autoComplete="current-password" value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent"
            placeholder="••••••••"
          />
        </div>
        <Button type="submit" variant="gradient" className="w-full" disabled={loading}>
          {loading && <Spinner />} Log in
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">
        Don't have an account? <Link to="/register" className="text-brand-600 font-medium hover:underline">Register</Link>
      </p>
    </AuthLayout>
  );
}

export function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm">
        <div className="flex justify-center mb-6">
          <Link to="/"><img src="/talkify-logo.png" alt="Talkify" className="h-8 w-auto" /></Link>
        </div>
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-8">
          <h1 className="text-xl font-bold text-ink text-center">{title}</h1>
          <p className="text-sm text-slate-500 text-center mt-1 mb-6">{subtitle}</p>
          {children}
        </div>
      </div>
    </div>
  );
}
