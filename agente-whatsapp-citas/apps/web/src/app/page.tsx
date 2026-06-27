'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { api, DashboardData } from '@/lib/api';
import { useEvents } from '@/lib/useEvents';
import { Card, PageTitle, fmtDateTime } from './ui';

function Metric({ label, value, hint }: { label: string; value: React.ReactNode; hint?: string }) {
  return (
    <Card style={{ flex: 1, minWidth: 160 }}>
      <div style={{ fontSize: 13, color: 'var(--muted)', fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 32, fontWeight: 700, marginTop: 6 }}>{value}</div>
      {hint && <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>{hint}</div>}
    </Card>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api
      .get<DashboardData>('/dashboard')
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => load(), [load]);
  useEvents(
    ['appointment.changed', 'patient.changed', 'conversation.changed', 'message.created', 'agent.changed'],
    () => load(),
  );

  if (error)
    return (
      <>
        <PageTitle>Inicio</PageTitle>
        <Card>
          <p>No se pudo conectar con el servidor.</p>
          <p style={{ color: 'var(--muted)', fontSize: 13 }}>{error}</p>
        </Card>
      </>
    );

  if (!data) return <PageTitle>Cargando…</PageTitle>;

  return (
    <>
      <PageTitle>Hola, {data.agent.centerName}</PageTitle>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
        <Metric label="Pacientes" value={data.patients} />
        <Metric label="Citas hoy" value={data.appointmentsToday} />
        <Metric label="Próximas citas" value={data.upcoming} />
        <Metric
          label="Estado del agente"
          value={
            <span style={{ color: data.agent.enabled ? 'var(--primary)' : '#b91c1c' }}>
              {data.agent.enabled ? 'Activo' : 'Pausado'}
            </span>
          }
          hint={data.agent.hasApiKey ? data.agent.model : 'Falta la API key'}
        />
      </div>

      <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>Conversaciones recientes</h2>
      <Card>
        {data.recentConversations.length === 0 && (
          <p style={{ color: 'var(--muted)' }}>Aún no hay conversaciones.</p>
        )}
        {data.recentConversations.map((c) => (
          <Link
            key={c.id}
            href="/conversaciones"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              padding: '10px 0',
              borderBottom: '1px solid var(--border)',
              textDecoration: 'none',
              color: 'var(--text)',
            }}
          >
            <span style={{ fontWeight: 600 }}>
              {c.title || 'Sin nombre'}{' '}
              <span style={{ fontSize: 12, color: 'var(--muted)', fontWeight: 400 }}>
                ({c.channel === 'whatsapp' ? 'WhatsApp' : 'Playground'})
              </span>
            </span>
            <span style={{ fontSize: 13, color: 'var(--muted)' }}>{fmtDateTime(c.lastMessageAt)}</span>
          </Link>
        ))}
      </Card>
    </>
  );
}
