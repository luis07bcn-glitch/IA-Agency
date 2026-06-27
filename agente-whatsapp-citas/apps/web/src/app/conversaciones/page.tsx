'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Conversation, Message, api } from '@/lib/api';
import { useEvents } from '@/lib/useEvents';
import { Card, PageTitle, fmtDateTime } from '../ui';

export default function ConversacionesPage() {
  const [threads, setThreads] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadThreads = useCallback(() => {
    api.get<Conversation[]>('/conversations').then(setThreads).catch(() => {});
  }, []);

  const loadMessages = useCallback((id: string) => {
    api.get<Message[]>(`/conversations/${id}/messages`).then(setMessages).catch(() => {});
  }, []);

  useEffect(() => loadThreads(), [loadThreads]);
  useEffect(() => {
    if (!activeId && threads.length) setActiveId(threads[0].id);
  }, [threads, activeId]);
  useEffect(() => {
    if (activeId) loadMessages(activeId);
  }, [activeId, loadMessages]);

  useEvents(['conversation.changed', 'message.created'], (_t, data) => {
    loadThreads();
    if (activeId && (!data?.conversationId || data.conversationId === activeId)) {
      loadMessages(activeId);
    }
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const active = threads.find((t) => t.id === activeId);

  return (
    <>
      <PageTitle>Conversaciones</PageTitle>
      <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 160px)' }}>
        {/* Thread list */}
        <Card style={{ width: 300, overflowY: 'auto', padding: 0 }}>
          {threads.length === 0 && <p style={{ color: 'var(--muted)', padding: 16 }}>Sin conversaciones.</p>}
          {threads.map((t) => (
            <div
              key={t.id}
              onClick={() => setActiveId(t.id)}
              style={{
                padding: 14,
                borderBottom: '1px solid var(--border)',
                cursor: 'pointer',
                background: t.id === activeId ? '#f0fdfa' : 'transparent',
              }}
            >
              <div style={{ fontWeight: 600, fontSize: 14 }}>{t.title || 'Sin nombre'}</div>
              <div style={{ fontSize: 12, color: 'var(--muted)', display: 'flex', justifyContent: 'space-between' }}>
                <span>{t.channel === 'whatsapp' ? '📱 WhatsApp' : '🧪 Playground'}</span>
                <span>{fmtDateTime(t.lastMessageAt)}</span>
              </div>
            </div>
          ))}
        </Card>

        {/* Messages */}
        <Card style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0 }}>
          {!active && <p style={{ color: 'var(--muted)', padding: 16 }}>Selecciona una conversación.</p>}
          {active && (
            <>
              <div style={{ padding: 14, borderBottom: '1px solid var(--border)', fontWeight: 700 }}>
                {active.title} {active.phone ? <span style={{ color: 'var(--muted)', fontWeight: 400, fontSize: 13 }}>· {active.phone}</span> : null}
              </div>
              <div style={{ flex: 1, overflowY: 'auto', padding: 16, background: '#f9fafb' }}>
                {messages.map((m) => (
                  <div
                    key={m.id}
                    style={{
                      display: 'flex',
                      justifyContent: m.role === 'user' ? 'flex-start' : 'flex-end',
                      marginBottom: 10,
                    }}
                  >
                    <div
                      style={{
                        maxWidth: '72%',
                        padding: '8px 12px',
                        borderRadius: 12,
                        fontSize: 14,
                        background: m.role === 'user' ? '#fff' : 'var(--primary)',
                        color: m.role === 'user' ? 'var(--text)' : '#fff',
                        border: m.role === 'user' ? '1px solid var(--border)' : 'none',
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {m.text}
                      <div style={{ fontSize: 10, opacity: 0.6, marginTop: 4 }}>{fmtDateTime(m.createdAt)}</div>
                    </div>
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>
              <div style={{ padding: 12, borderTop: '1px solid var(--border)', fontSize: 12, color: 'var(--muted)' }}>
                Esta es una bandeja de solo lectura. Para chatear con el agente usa el Playground en la pantalla «Agente».
              </div>
            </>
          )}
        </Card>
      </div>
    </>
  );
}
