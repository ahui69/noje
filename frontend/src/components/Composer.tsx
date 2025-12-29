import { useEffect, useRef, useState } from 'react';

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
  uploading?: boolean;
  onUpload?: (files: FileList) => void;
  attachments?: { id: string; name: string }[];
  onRemoveAttachment?: (id: string) => void;
}

export default function Composer({
  value,
  onChange,
  onSend,
  disabled,
  uploading,
  onUpload,
  attachments = [],
  onRemoveAttachment,
}: Props) {
  const ref = useRef<HTMLTextAreaElement | null>(null);
  const [rows, setRows] = useState(3);

  useEffect(() => {
    if (!ref.current) return;
    ref.current.style.height = 'auto';
    ref.current.style.height = `${ref.current.scrollHeight}px`;
    setRows(Math.min(10, Math.max(3, Math.ceil(ref.current.scrollHeight / 24))));
  }, [value]);

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="border border-subtle/70 rounded-lg bg-panel p-3 space-y-3">
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {attachments.map((f) => (
            <span
              key={f.id}
              className="px-2 py-1 text-xs rounded bg-subtle text-gray-200 flex items-center gap-2"
            >
              {f.name}
              {onRemoveAttachment && (
                <button
                  className="text-gray-400 hover:text-white"
                  onClick={() => onRemoveAttachment(f.id)}
                >
                  ✕
                </button>
              )}
            </span>
          ))}
        </div>
      )}
      <textarea
        ref={ref}
        className="w-full bg-transparent text-sm outline-none resize-none"
        placeholder="Napisz wiadomość..."
        rows={rows}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKey}
      />
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {onUpload && (
            <label className="text-xs px-2 py-1 border border-subtle rounded cursor-pointer hover:bg-subtle/60">
              <input
                type="file"
                className="hidden"
                multiple
                onChange={(e) => {
                  if (e.target.files) onUpload(e.target.files);
                  e.target.value = '';
                }}
              />
              Dodaj plik
            </label>
          )}
          {uploading && <span className="text-xs text-gray-400">Upload…</span>}
        </div>
        <button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className={`px-4 py-2 rounded font-semibold ${
            disabled || !value.trim() ? 'bg-subtle text-gray-500 cursor-not-allowed' : 'bg-accent text-white hover:opacity-90'
          }`}
        >
          Wyślij
        </button>
      </div>
    </div>
  );
}
