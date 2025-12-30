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
      {messages.map((m, idx) => {
        const isUser = m.role === 'user';
        return (
          <div key={`${m.role}-${idx}-${m.ts || idx}`} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-3xl w-full sm:w-11/12 rounded-lg border shadow-sm transition-colors ${
                isUser
                  ? 'border-accent/60 bg-accent/10 text-white'
                  : 'border-subtle bg-subtle/70 text-gray-50'
              }`}
            >
              <div className="flex justify-between items-center px-4 pt-3 text-xs uppercase tracking-wide text-gray-300">
                <span>{m.role}</span>
                {onCopy && (
                  <button
                    className="text-[11px] text-gray-200 hover:text-white underline-offset-2 hover:underline"
                    onClick={() => onCopy(m.content)}
                  >
                    Kopiuj
                  </button>
                )}
              </div>
              <div className="px-4 pb-4 pt-2 prose prose-invert max-w-none text-sm break-words whitespace-pre-wrap prose-pre:whitespace-pre-wrap prose-code:break-words">
                <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                  {m.content}
                </ReactMarkdown>
              </div>
              {m.attachments && m.attachments.length > 0 && (
                <div className="px-4 pb-3 space-y-1 text-xs text-gray-200">
                  <p className="font-semibold">Załączniki</p>
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
          </div>
        );
      })}
    </div>
  );
}
