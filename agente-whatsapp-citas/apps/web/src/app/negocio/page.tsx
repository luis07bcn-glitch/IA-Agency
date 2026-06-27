'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, InsightAnswer, BusinessReport } from '@/lib/api';

function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 12, padding: 20, ...style }}>
      {children}
    </div>
  );
}

function Button({
  children, onClick, disabled, variant = 'primary',
}: { children: React.ReactNode; onClick?: () => void; disabled?: boolean; variant?: 'primary' | 'ghost' }) {
  return (
    <button onClick={onClick} disabled={disabled}
      style={{
        padding: '10px 18px', borderRadius: 8,
        border: variant === 'ghost' ? '1px solid var(--border)' : 'none',
        background: variant === 'ghost' ? 'transparent' : 'var(--primary)',
        color: variant === 'ghost' ? 'var(--text)' : '#fff',
        fontWeight: 700, fontSize: 14, cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.6 : 1,
      }}>
      {children}
    </button>
  );
}

const PERIODS = [
  { days: 7, label: '7 días' },
  { days: 30, label: '30 días' },
  { days: 90, label: '90 días' },
];

const CAT_COLORS: Record<string, string> = {
  'Demanda no cubierta': '#3b82f6',
  'Queja/fricción': '#ef4444',
  Competencia: '#f59e0b',
  'Pregunta sin resolver': '#8b5cf6',
  'Oportunidad de ingreso': '#10b981',
};

type Qa = { q: string; a: string | null; meta?: InsightAnswer['basedOn'] };

export default function NegocioPage() {
  const [days, setDays] = useState(30);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [question, setQuestion] = useState('');
  const [thread, setThread] = useState<Qa[]>([]);
  const [asking, setAsking] = useState(false);

  const [report, setReport] = useState<BusinessReport | null>(null);
  const [reportState, setReportState] = useState<'idle' | 'loading' | 'error'>('idle');
  const [sendState, setSendState] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');

  useEffect(() => {
    api.get<{ questions: string[] }>('/insights/suggestions').then((r) => setSuggestions(r.questions)).catch(() => undefined);
  }, []);

  const ask = useCallback(async (q: string) => {
    const text = q.trim();
    if (!text || asking) return;
    setQuestion('');
    setThread((t) => [{ q: text, a: null }, ...t]);
    setAsking(true);
    try {
      const r = await api.post<InsightAnswer>('/insights/ask', { question: text, days });
      setThread((t) => t.map((item, i) => (i === 0 ? { ...item, a: r.answer, meta: r.basedOn } : item)));
    } catch (e) {
      setThread((t) => t.map((item, i) => (i === 0 ? { ...item, a: `⚠️ ${e instanceof Error ? e.message : 'Error'}` } : item)));
    } finally {
      setAsking(false);
    }
  }, [asking, days]);

  const genReport = useCallback(async () => {
    setReportState('loading');
    try {
      const r = await api.get<BusinessReport>(`/insights/report?days=${days}`);
      setReport(r);
      setReportState('idle');
    } catch {
      setReportState('error');
    }
  }, [days]);

  const sendWhatsApp = useCallback(async () => {
    setSendState('sending');
    try {
      await api.post('/metrics/weekly-insights-send', {});
      setSendState('sent');
      setTimeout(() => setSendState('idle'), 4000);
    } catch {
      setSendState('error');
      setTimeout(() => setSendState('idle'), 4000);
    }
  }, []);

  return (
    <div style={{ maxWidth: 920, margin: '0 auto', padding: '32px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontWeight: 800, fontSize: 26, margin: 0 }}>🧠 Habla con tu negocio</h1>
          <p style={{ color: 'var(--muted)', margin: '4px 0 0', fontSize: 14 }}>
            Pregúntale lo que quieras: las respuestas salen de lo que de verdad dicen tus clientes.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {PERIODS.map((p) => (
            <button key={p.days} onClick={() => setDays(p.days)}
              style={{
                padding: '7px 14px', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer',
                border: days === p.days ? '2px solid var(--primary)' : '1px solid var(--border)',
                background: days === p.days ? 'var(--primary)' : 'transparent',
                color: days === p.days ? '#fff' : 'var(--text)',
              }}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* ASK */}
      <Card style={{ margin: '20px 0' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            value={question} onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && ask(question)}
            placeholder="Ej: ¿qué me piden mis clientes que no ofrezco?"
            style={{ flex: 1, padding: '12px 14px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 15, background: 'var(--bg)', color: 'var(--text)' }}
          />
          <Button onClick={() => ask(question)} disabled={asking || !question.trim()}>
            {asking ? 'Pensando…' : 'Preguntar'}
          </Button>
        </div>

        {suggestions.length > 0 && thread.length === 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 14 }}>
            {suggestions.map((s, i) => (
              <button key={i} onClick={() => ask(s)} disabled={asking}
                style={{ fontSize: 13, padding: '7px 12px', borderRadius: 20, background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)', cursor: asking ? 'default' : 'pointer' }}>
                {s}
              </button>
            ))}
          </div>
        )}

        {thread.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 18 }}>
            {thread.map((item, i) => (
              <div key={i} style={{ borderTop: i > 0 ? '1px solid var(--border)' : 'none', paddingTop: i > 0 ? 14 : 0 }}>
                <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6 }}>❓ {item.q}</div>
                {item.a === null ? (
                  <div style={{ color: 'var(--muted)', fontSize: 14, fontStyle: 'italic' }}>Analizando conversaciones…</div>
                ) : (
                  <>
                    <div style={{ fontSize: 14.5, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{item.a}</div>
                    {item.meta && (
                      <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 6 }}>
                        Basado en {item.meta.conversations} conversación(es) de los últimos {item.meta.periodDays} días.
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* REPORT */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
        <h2 style={{ fontWeight: 800, fontSize: 19, margin: 0 }}>📋 Informe: lo que te están diciendo</h2>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button
            onClick={sendWhatsApp}
            disabled={sendState === 'sending'}
            title="Enviar informe de los últimos 7 días por WhatsApp al dueño"
            style={{
              padding: '9px 14px', borderRadius: 8, fontSize: 13, fontWeight: 600,
              border: '1px solid var(--border)',
              background: sendState === 'sent' ? '#10b981' : sendState === 'error' ? '#ef4444' : 'transparent',
              color: sendState === 'sent' || sendState === 'error' ? '#fff' : 'var(--text)',
              cursor: sendState === 'sending' ? 'not-allowed' : 'pointer',
              opacity: sendState === 'sending' ? 0.6 : 1,
            }}
          >
            {sendState === 'sending' ? '📤 Enviando…' : sendState === 'sent' ? '✅ Enviado' : sendState === 'error' ? '❌ Error' : '📲 Enviar por WhatsApp'}
          </button>
          <Button variant="ghost" onClick={genReport} disabled={reportState === 'loading'}>
            {reportState === 'loading' ? 'Generando…' : report ? 'Regenerar' : 'Generar informe'}
          </Button>
        </div>
      </div>

      {reportState === 'error' && (
        <Card style={{ borderColor: '#ef4444' }}>No se pudo generar el informe. Revisa la API key del modelo e inténtalo de nuevo.</Card>
      )}

      {report && reportState !== 'loading' && (
        <>
          <Card style={{ marginBottom: 14, background: 'linear-gradient(135deg, var(--primary), #6b46c1)', border: 'none', color: '#fff' }}>
            <div style={{ fontSize: 13, opacity: 0.9, marginBottom: 4 }}>TITULAR DE LA SEMANA</div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{report.summary}</div>
            <div style={{ fontSize: 12, opacity: 0.85, marginTop: 8 }}>
              Analizadas {report.basedOn.conversations} conversación(es) · {report.basedOn.periodDays} días
            </div>
          </Card>

          {report.findings.length === 0 ? (
            <Card style={{ color: 'var(--muted)' }}>
              Aún no hay suficientes conversaciones para sacar conclusiones. Cuando el asistente atienda a más clientes, aquí verás los patrones.
            </Card>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {report.findings.map((f, i) => {
                const color = CAT_COLORS[f.category] ?? 'var(--muted)';
                return (
                  <Card key={i}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                      <span style={{ fontSize: 22 }}>{f.emoji}</span>
                      <div>
                        <span style={{ fontSize: 11, fontWeight: 700, color, background: `${color}22`, padding: '2px 8px', borderRadius: 12 }}>
                          {f.category}
                        </span>
                        <div style={{ fontWeight: 700, fontSize: 15.5, marginTop: 4 }}>{f.title}</div>
                      </div>
                    </div>
                    {f.detail && <div style={{ fontSize: 14, lineHeight: 1.5, marginBottom: f.quote || f.action ? 8 : 0 }}>{f.detail}</div>}
                    {f.quote && (
                      <div style={{ fontSize: 13.5, fontStyle: 'italic', color: 'var(--muted)', borderLeft: `3px solid ${color}`, paddingLeft: 10, margin: '8px 0' }}>
                        “{f.quote}”
                      </div>
                    )}
                    {f.action && (
                      <div style={{ fontSize: 13.5, marginTop: 8, background: 'var(--bg)', borderRadius: 8, padding: '8px 12px' }}>
                        💡 <strong>Qué hacer:</strong> {f.action}
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          )}
        </>
      )}

      {!report && reportState === 'idle' && (
        <Card style={{ color: 'var(--muted)', textAlign: 'center', padding: '32px 20px' }}>
          Pulsa <strong>Generar informe</strong> para que el asistente analice las conversaciones del periodo y te diga qué demandan tus clientes, por qué cancelan y dónde hay oportunidades.
        </Card>
      )}
    </div>
  );
}
