import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Button, ErrorBanner, Spinner } from '../components/ui';
import { AuthLayout } from './Login';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const passwordTooShort = password.length > 0 && password.length < 8;
  const passwordsMismatch = confirm.length > 0 && password !== confirm;

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password.length < 8) return setError('Password must be at least 8 characters.');
    if (password !== confirm) return setError('Passwords do not match.');

    setLoading(true);
    try {
      await register(name, email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Create your account" subtitle="Start chatting with your documents in minutes.">
      <form onSubmit={onSubmit} className="space-y-4">
        <ErrorBanner message={error} />
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
          <input
            required value={name} onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            placeholder="Jane Doe"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
          <input
            type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            placeholder="you@example.com"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
          <input
            type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
            className={`w-full rounded-lg border px-3 py-2.5 text-sm focus:outline-none focus:ring-2 ${passwordTooShort ? 'border-red-300 focus:ring-red-300' : 'border-slate-300 focus:ring-brand-400'}`}
            placeholder="At least 8 characters"
          />
          {passwordTooShort && <p className="text-xs text-red-600 mt-1">Must be at least 8 characters.</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Confirm password</label>
          <input
            type="password" required value={confirm} onChange={(e) => setConfirm(e.target.value)}
            className={`w-full rounded-lg border px-3 py-2.5 text-sm focus:outline-none focus:ring-2 ${passwordsMismatch ? 'border-red-300 focus:ring-red-300' : 'border-slate-300 focus:ring-brand-400'}`}
            placeholder="Re-enter your password"
          />
          {passwordsMismatch && <p className="text-xs text-red-600 mt-1">Passwords don't match.</p>}
        </div>
        <Button type="submit" variant="gradient" className="w-full" disabled={loading}>
          {loading && <Spinner />} Create account
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">
        Already have an account? <Link to="/login" className="text-brand-600 font-medium hover:underline">Log in</Link>
      </p>
    </AuthLayout>
  );
}
