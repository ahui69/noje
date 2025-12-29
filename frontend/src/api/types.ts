export interface ChatRequest {
  message?: string;
  messages?: { role: 'user' | 'assistant' | 'system'; content: string }[];
  session_id?: string;
  user_id?: string;
  temperature?: number;
  max_tokens?: number;
  use_history?: boolean;
  system_prompt?: string | null;
}

export interface ChatResponse {
  answer: string;
  session_id: string;
  ts: number;
  metadata: {
    model: string;
    base_url: string;
    history_used: boolean;
  };
}

export interface SessionSummary {
  id: string;
  user_id: string;
  title?: string | null;
  created_at: number;
  updated_at: number;
  messages: number;
}

export interface SessionDetail {
  session_id: string;
  user_id: string;
  title?: string | null;
  created_at: number;
  updated_at: number;
  messages: { role: string; content: string; ts: number }[];
}

export interface FileInfo {
  id?: string;
  file_id?: string;
  name: string;
  filename?: string;
  path?: string;
  size?: number;
  uploaded_at?: number;
  mime?: string;
}

export interface UploadResponse {
  ok: boolean;
  file_id: string;
  filename: string;
  size: number;
  path?: string;
  analysis?: Record<string, unknown>;
}

export interface HealthPayload {
  status: string;
  version?: string;
  ts?: number;
  env?: Record<string, unknown>;
  metrics?: Record<string, unknown>;
}

export interface STTResponse {
  ok: boolean;
  text: string;
  language?: string;
  duration?: number;
}

export interface TTSStatus {
  ok: boolean;
  provider: string;
  voice_id_set: boolean;
  api_key_set: boolean;
  ts: number;
}
