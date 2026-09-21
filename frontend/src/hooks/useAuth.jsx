import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api, setToken } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    try {
      const me = await api.me();
      setUser(me);
    } catch {
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const hasToken = !!localStorage.getItem('talkify_token');
    if (hasToken) {
      loadUser();
    } else {
      setLoading(false);
    }
  }, [loadUser]);

  const login = async (email, password) => {
    const { access_token } = await api.login({ email, password });
    setToken(access_token);
    await loadUser();
  };

  const register = async (name, email, password) => {
    const { access_token } = await api.register({ name, email, password });
    setToken(access_token);
    await loadUser();
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
