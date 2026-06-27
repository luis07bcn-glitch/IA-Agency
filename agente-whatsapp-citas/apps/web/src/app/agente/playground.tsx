'use client';

import { useRef, useState } from 'react';
import { api } from '@/lib/api';
import { Button, Card, Input } from '../ui';

interface ChatMsg { role: 'user' | 'assistant'; text: string }

export function Playground() {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', text }]);
    setLoading(true);
    try {
      const res = await api.post<{ conversationId: string; reply: string }>('/agent/playground', {
        message: text,
        conversationId,
      });
      setConversationId(res.conversationId);
      setMessages((m) => [...m, { role: 'assistant', text: res.reply }]);
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', text: 'Error: ' + (e as Error).message }]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  };

  const reset = () => {
    setMessages([]);
    setConversationId(undefined);
  };

  return (
    <Card style={{ padding: 0, maxWidth: 720 }}>
      <div style={{ height: 360, overflowY: 'auto', padding: 16, background: '#f9fafb' }}>
        {messages.length === 0 && (
          <p style={{ color: 'var(--muted)', fontSize: 14 }}>
            Escribe un mensaje para empezar. Prueba: «Hola, me molesta el hombro, ¿tenéis hueco esta semana?»
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-start' : 'flex-end', marginBottom: 10 }}>
            <div
              style={{
                maxWidth: '72%',
                padding: '8px 12px',
                borderRadius: 12,
                fontSize: 14,
                whiteSpace: 'pre-wrap',
                background: m.role === 'user' ? '#fff' : 'var(--primary)',
                color: m.role === 'user' ? 'var(--text)' : '#fff',
                border: m.role === 'user' ? '1px solid var(--border)' : 'none',
              }}
            >
              {m.text}
            </div>
          </div>
        ))}
        {loading && <div style={{ fontSize: 13, color: 'var(--muted)' }}>El agente está escribiendo…</div>}
        <div ref={bottomRef} />
      </div>
      <div style={{ display: 'flex', gap: 8, padding: 12, borderTop: '1px solid var(--border)' }}>
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') send(); }}
          placeholder="Escribe un mensaje…"
        />
        <Button onClick={send} disabled={loading}>Enviar</Button>
        <Button variant="ghost" onClick={reset}>Reiniciar</Button>
      </div>
    </Card>
  );
}
