const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getToken() {
  return localStorage.getItem('talkify_token');
}

export function setToken(token) {
  if (token) localStorage.setItem('talkify_token', token);
  else localStorage.removeItem('talkify_token');
}

async function request(path, { method = 'GET', body, isForm = false } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!isForm && body) headers['Content-Type'] = 'application/json';

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: isForm ? body : body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return null;

  let data = null;
  try {
    data = await res.json();
  } catch {
    // no body
  }

  if (!res.ok) {
    const message = data?.detail || `Request failed (${res.status})`;
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
  }
  return data;
}

export const api = {
  register: (payload) => request('/api/auth/register', { method: 'POST', body: payload }),
  login: (payload) => request('/api/auth/login', { method: 'POST', body: payload }),
  me: () => request('/api/auth/me'),

  listDocuments: () => request('/api/documents'),
  getDocument: (id) => request(`/api/documents/${id}`),
  deleteDocument: (id) => request(`/api/documents/${id}`, { method: 'DELETE' }),
  uploadDocument: (file) => {
    const form = new FormData();
    form.append('file', file);
    return request('/api/documents', { method: 'POST', body: form, isForm: true });
  },

  listConversations: () => request('/api/chat/conversations'),
  createConversation: (payload) => request('/api/chat/conversations', { method: 'POST', body: payload }),
  deleteConversation: (id) => request(`/api/chat/conversations/${id}`, { method: 'DELETE' }),
  getMessages: (id) => request(`/api/chat/conversations/${id}/messages`),
  ask: (id, question) => request(`/api/chat/conversations/${id}/ask`, { method: 'POST', body: { question } }),
  giveFeedback: (messageId, payload) => request(`/api/chat/messages/${messageId}/feedback`, { method: 'POST', body: payload }),

  analyticsSummary: () => request('/api/analytics/summary'),
};
