import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ChatMessage({ message, onFeedback }) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState(null);

  const copy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const sendFeedback = (rating) => {
    setFeedbackGiven(rating);
    onFeedback?.(message.id, rating);
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : ''}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser ? 'bg-brand-gradient text-white whitespace-pre-wrap' : 'bg-white border border-slate-200 text-slate-800'
          }`}
        >
          {isUser ? (
            message.content
          ) : (
            <div className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {!isUser && message.citations?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {message.citations.map((c) => (
              <span
                key={c.index}
                title={c.excerpt}
                className="inline-flex items-center gap-1 text-xs bg-slate-100 text-slate-600 rounded-full px-2.5 py-1 cursor-default hover:bg-slate-200 transition-colors"
              >
                [{c.index}] {c.source_name} · p.{c.page}
              </span>
            ))}
          </div>
        )}

        {!isUser && (
          <div className="mt-1.5 flex items-center gap-3 text-xs text-slate-400">
            <button onClick={copy} className="hover:text-slate-600">{copied ? 'Copied!' : 'Copy'}</button>
            <button
              onClick={() => sendFeedback('helpful')}
              className={`hover:text-emerald-600 ${feedbackGiven === 'helpful' ? 'text-emerald-600' : ''}`}
            >
              👍 Helpful
            </button>
            <button
              onClick={() => sendFeedback('not_helpful')}
              className={`hover:text-red-600 ${feedbackGiven === 'not_helpful' ? 'text-red-600' : ''}`}
            >
              👎 Not helpful
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
