import AppShell from '../components/AppShell';
import { Button } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

export default function Settings() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-ink">Settings</h1>

        <section className="mt-6 bg-white border border-slate-200 rounded-xl p-6">
          <h2 className="font-semibold text-ink">Profile</h2>
          <div className="mt-4 space-y-3 text-sm">
            <Row label="Name" value={user?.name} />
            <Row label="Email" value={user?.email} />
          </div>
        </section>

        <section className="mt-6 bg-white border border-slate-200 rounded-xl p-6">
          <h2 className="font-semibold text-ink">Privacy</h2>
          <p className="text-sm text-slate-500 mt-2">
            Your documents and conversations are visible only to your account —
            every query on the backend is scoped by your user ID. Deleting a
            document removes its file, its extracted text, its search indexes,
            and any citations pointing to it.
          </p>
        </section>

        <section className="mt-6 bg-white border border-red-200 rounded-xl p-6">
          <h2 className="font-semibold text-red-700">Account</h2>
          <p className="text-sm text-slate-500 mt-2">Log out of Talkify on this device.</p>
          <Button variant="danger" className="mt-3" onClick={() => { logout(); navigate('/login'); }}>
            Log out
          </Button>
        </section>
      </div>
    </AppShell>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-slate-50 pb-2">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-800">{value}</span>
    </div>
  );
}
