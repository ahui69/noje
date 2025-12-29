import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  ts?: number;
}

export default function MessageList({ messages, onCopy }: { messages: Message[]; onCopy?: (text: string) => void }) {
  return (
    <div className="flex-1 overflow-y-auto space-y-4 pr-2">
      {messages.map((m, idx) => (
        <div
          key={`${m.role}-${idx}-${m.ts || idx}`}
          className={`p-4 rounded-lg border ${m.role === 'assistant' ? 'border-subtle bg-subtle/60' : 'border-subtle/40 bg-transparent'}`}
        >
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs uppercase tracking-wide text-gray-400">{m.role}</span>
            {onCopy && (
              <button
                className="text-xs text-gray-300 hover:text-white"
                onClick={() => onCopy(m.content)}
              >
                Kopiuj
              </button>
            )}
          </div>
          <div className="prose prose-invert max-w-none text-sm">
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
              {m.content}
            </ReactMarkdown>
          </div>
        </div>
      ))}
    </div>
  );
}
