import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  ts?: number;
  attachments?: { file_id?: string; name?: string; filename?: string }[];
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
          <div className="prose prose-invert max-w-none text-sm break-words whitespace-pre-wrap prose-pre:whitespace-pre-wrap prose-code:break-words">
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
              {m.content}
            </ReactMarkdown>
          </div>
          {m.attachments && m.attachments.length > 0 && (
            <div className="mt-3 space-y-1 text-xs text-gray-300">
              <p className="font-semibold text-gray-200">Załączniki</p>
              <ul className="list-disc list-inside space-y-1">
                {m.attachments.map((a, i) => (
                  <li key={`${a.file_id || a.name || i}`} className="truncate">
                    {a.name || a.filename || a.file_id}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
