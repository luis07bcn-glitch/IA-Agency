'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { api, GeneratedDemo, AgentConfig } from '@/lib/api';

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

const DAYS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
const BUILD_STEPS = [
  '🔎 Buscando el negocio en Google…',
  '🌐 Leyendo su web y sus reseñas…',
  '🧠 Configurando su asistente…',
];

type Msg = { role: 'user' | 'assistant'; content: string };

export default function DemoPage() {
  const [configured, setConfigured] = useState(true);
  const [name, setName] = useState('');
  const [city, setCity] = useState('');
  const [phase, setPhase] = useState<'form' | 'building' | 'result'>('form');
  const [buildStep, setBuildStep] = useState(0);
  const [demo, setDemo] = useState<GeneratedDemo | null>(null);
  const [error, setError] = useState('');

  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [applyState, setApplyState] = useState<'idle' | 'applying' | 'done'>('idle');
  const [showKb, setShowKb] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [liveName, setLiveName] = useState<string | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get<{ configured: boolean }>('/demo/status').then((r) => setConfigured(r.configured)).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, sending]);

  const build = useCallback(async () => {
    if (!name.trim()) return;
    setError('');
    setPhase('building');
    setBuildStep(0);
    const ticker = setInterval(() => setBuildStep((s) => Math.min(s + 1, BUILD_STEPS.length - 1)), 1800);
    try {
      const result = await api.post<GeneratedDemo>('/demo/build', { name: name.trim(), city: city.trim() });
      clearInterval(ticker);
      if (!result.found) {
        setError('No encontramos ese negocio en Google. Prueba a añadir la ciudad o un nombre más preciso.');
        setPhase('form');
        return;
      }
      setDemo(result);
      setMessages(result.welcomeMessage ? [{ role: 'assistant', content: result.welcomeMessage }] : []);
      setApplyState('idle');
      setPhase('result');
    } catch (e) {
      clearInterval(ticker);
      setError(e instanceof Error ? e.message : 'Error generando la demo.');
      setPhase('form');
    }
  }, [name, city]);

  const send = useCallback(async () => {
    if (!input.trim() || !demo || sending) return;
    const text = input.trim();
    setInput('');
    const next = [...messages, { role: 'user' as const, content: text }];
    setMessages(next);
    setSending(true);
    try {
      const r = await api.post<{ reply: string }>('/demo/chat', {
        config: demo.config,
        knowledgeBase: demo.knowledgeBase,
        history: next,
        message: text,
      });
      setMessages((m) => [...m, { role: 'assistant', content: r.reply }]);
    } catch {
      setMessages((m) => [...m, { role: 'assistant', content: 'Ups, error técnico en la demo. Inténtalo de nuevo.' }]);
    } finally {
      setSending(false);
    }
  }, [input, demo, messages, sending]);

  const openConfirm = useCallback(() => {
    setConfirmOpen(true);
    // Fetch the live agent name so the warning shows exactly what gets replaced.
    api.get<AgentConfig>('/config').then((c) => setLiveName(c.centerName)).catch(() => setLiveName(null));
  }, []);

  const apply = useCallback(async () => {
    if (!demo) return;
    setApplyState('applying');
    try {
      await api.post('/demo/apply', { config: demo.config, knowledgeBase: demo.knowledgeBase });
      setApplyState('done');
      setConfirmOpen(false);
    } catch {
      setApplyState('idle');
    }
  }, [demo]);

  const reset = () => {
    setDemo(null);
    setMessages([]);
    setPhase('form');
    setError('');
    setName('');
    setCity('');
  };

  return (
    <div style={{ maxWidth: 1040, margin: '0 auto', padding: '32px 20px' }}>
      <h1 style={{ fontWeight: 800, fontSize: 26, margin: 0 }}>⚡ Demo Instantánea</h1>
      <p style={{ color: 'var(--muted)', margin: '4px 0 24px', fontSize: 14 }}>
        Escribe el nombre de un negocio y en segundos tendrás un asistente que ya lo conoce — listo para enseñárselo al dueño.
      </p>

      {!configured && (
        <Card style={{ marginBottom: 20, borderColor: '#f59e0b' }}>
          <strong>Falta configurar Google Places.</strong> Añade <code>GOOGLE_PLACES_API_KEY</code> en el archivo <code>.env</code> y reinicia el backend.
        </Card>
      )}

      {/* FORM */}
      {phase === 'form' && (
        <Card style={{ background: 'linear-gradient(135deg, var(--primary), #6b46c1)', border: 'none', color: '#fff' }}>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 14, opacity: 0.95 }}>
            ¿Qué negocio quieres convertir en agente?
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <input
              value={name} onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && build()}
              placeholder="Nombre del negocio (ej: Restaurante Botafumeiro)"
              style={{ flex: 2, minWidth: 240, padding: '12px 14px', borderRadius: 8, border: 'none', fontSize: 15 }}
            />
            <input
              value={city} onChange={(e) => setCity(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && build()}
              placeholder="Ciudad"
              style={{ flex: 1, minWidth: 140, padding: '12px 14px', borderRadius: 8, border: 'none', fontSize: 15 }}
            />
            <button onClick={build} disabled={!name.trim()}
              style={{ padding: '12px 22px', borderRadius: 8, border: 'none', background: '#0f172a', color: '#fff', fontWeight: 800, fontSize: 15, cursor: name.trim() ? 'pointer' : 'not-allowed', opacity: name.trim() ? 1 : 0.6 }}>
              Generar agente →
            </button>
          </div>
          {error && <p style={{ marginTop: 12, marginBottom: 0, fontSize: 13, background: 'rgba(0,0,0,0.25)', padding: '8px 12px', borderRadius: 8 }}>{error}</p>}
        </Card>
      )}

      {/* BUILDING */}
      {phase === 'building' && (
        <Card style={{ textAlign: 'center', padding: '48px 20px' }}>
          <div style={{ fontSize: 40, marginBottom: 16 }} className="demo-spin">⚙️</div>
          <div style={{ display: 'inline-flex', flexDirection: 'column', gap: 10, textAlign: 'left' }}>
            {BUILD_STEPS.map((s, i) => (
              <div key={i} style={{ fontSize: 15, fontWeight: i === buildStep ? 700 : 400, color: i < buildStep ? '#48bb78' : i === buildStep ? 'var(--text)' : 'var(--muted)' }}>
                {i < buildStep ? '✅ ' : i === buildStep ? '⏳ ' : '◻️ '}
                {s.replace(/^.. /, '')}
              </div>
            ))}
          </div>
          <style>{`.demo-spin{animation:demospin 1.6s linear infinite}@keyframes demospin{to{transform:rotate(360deg)}}`}</style>
        </Card>
      )}

      {/* RESULT */}
      {phase === 'result' && demo && (
        <>
          <Card style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <div style={{ fontSize: 20, fontWeight: 800 }}>{demo.source.name}</div>
              <div style={{ fontSize: 13, color: 'var(--muted)' }}>
                {demo.source.primaryType ?? 'Negocio'}
                {demo.source.rating ? ` · ⭐ ${demo.source.rating} (${demo.source.userRatingCount})` : ''}
                {demo.source.address ? ` · ${demo.source.address}` : ''}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <Button variant="ghost" onClick={reset}>Probar otro</Button>
              {applyState === 'done' ? (
                <span style={{ color: '#48bb78', fontWeight: 700, fontSize: 14 }}>✓ Aplicado a tu agente</span>
              ) : (
                <Button onClick={openConfirm} disabled={applyState === 'applying'}>
                  {applyState === 'applying' ? 'Aplicando…' : 'Aplicar a mi agente'}
                </Button>
              )}
            </div>
          </Card>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16, alignItems: 'start' }}>
            {/* LEARNED */}
            <Card>
              <h3 style={{ fontWeight: 700, marginTop: 0, marginBottom: 12 }}>🧠 Lo que ha aprendido</h3>
              {demo.highlights.length > 0 && (
                <ul style={{ margin: '0 0 16px', paddingLeft: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {demo.highlights.map((h, i) => (
                    <li key={i} style={{ fontSize: 14 }}>✅ {h}</li>
                  ))}
                </ul>
              )}

              {demo.config.services.length > 0 && (
                <>
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--muted)', marginBottom: 6 }}>SERVICIOS RESERVABLES</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
                    {demo.config.services.map((s, i) => (
                      <span key={i} style={{ fontSize: 12, padding: '4px 10px', borderRadius: 20, background: 'var(--bg)', border: '1px solid var(--border)' }}>
                        {s.name} · {s.durationMin}′
                      </span>
                    ))}
                  </div>
                </>
              )}

              {demo.config.schedule.length > 0 && (
                <>
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--muted)', marginBottom: 6 }}>HORARIO</div>
                  <div style={{ fontSize: 13, marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {demo.config.schedule
                      .slice()
                      .sort((a, b) => ((a.weekday || 7) - (b.weekday || 7)))
                      .map((d, i) => (
                        <div key={i}>
                          <strong>{DAYS[d.weekday]}:</strong>{' '}
                          {d.intervals.length ? d.intervals.map((iv) => `${iv.start}-${iv.end}`).join(', ') : 'cerrado'}
                        </div>
                      ))}
                  </div>
                </>
              )}

              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', fontSize: 13, marginBottom: demo.knowledgeBase ? 14 : 0 }}>
                {demo.source.website && <a href={demo.source.website} target="_blank" rel="noreferrer" style={{ color: 'var(--primary)' }}>🌐 Web</a>}
                {demo.source.googleMapsUri && <a href={demo.source.googleMapsUri} target="_blank" rel="noreferrer" style={{ color: 'var(--primary)' }}>📍 Google Maps</a>}
                {demo.source.phone && <span style={{ color: 'var(--muted)' }}>📞 {demo.source.phone}</span>}
              </div>

              {demo.knowledgeBase && (
                <div>
                  <button onClick={() => setShowKb((v) => !v)}
                    style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: 13, fontWeight: 600, padding: 0 }}>
                    {showKb ? '▾ Ocultar ficha de información' : '▸ Ver ficha de información'}
                  </button>
                  {showKb && (
                    <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12.5, color: 'var(--muted)', marginTop: 8, fontFamily: 'inherit' }}>{demo.knowledgeBase}</pre>
                  )}
                </div>
              )}
            </Card>

            {/* CHAT */}
            <Card style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', height: 540 }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', fontWeight: 700, fontSize: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                💬 Habla con el asistente <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--muted)' }}>(como lo haría un cliente)</span>
              </div>
              <div ref={chatRef} style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 10, background: 'var(--bg)' }}>
                {messages.map((m, i) => (
                  <div key={i} style={{ alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '82%' }}>
                    <div style={{
                      padding: '9px 13px', borderRadius: 14, fontSize: 14, lineHeight: 1.4,
                      background: m.role === 'user' ? 'var(--primary)' : 'var(--card)',
                      color: m.role === 'user' ? '#fff' : 'var(--text)',
                      border: m.role === 'user' ? 'none' : '1px solid var(--border)',
                      borderBottomRightRadius: m.role === 'user' ? 4 : 14,
                      borderBottomLeftRadius: m.role === 'user' ? 14 : 4,
                      whiteSpace: 'pre-wrap',
                    }}>
                      {m.content}
                    </div>
                  </div>
                ))}
                {sending && <div style={{ alignSelf: 'flex-start', color: 'var(--muted)', fontSize: 13, fontStyle: 'italic' }}>escribiendo…</div>}
              </div>
              <div style={{ display: 'flex', gap: 8, padding: 12, borderTop: '1px solid var(--border)' }}>
                <input
                  value={input} onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && send()}
                  placeholder="Escribe como si fueras un cliente…"
                  disabled={sending}
                  style={{ flex: 1, padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 14, background: 'var(--bg)', color: 'var(--text)' }}
                />
                <Button onClick={send} disabled={sending || !input.trim()}>Enviar</Button>
              </div>
            </Card>
          </div>
        </>
      )}

      {/* CONFIRM APPLY */}
      {confirmOpen && demo && (
        <div
          onClick={() => applyState !== 'applying' && setConfirmOpen(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: 20 }}
        >
          <div onClick={(e) => e.stopPropagation()}
            style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: 24, maxWidth: 460, width: '100%' }}>
            <div style={{ fontSize: 22, marginBottom: 8 }}>⚠️ Configurar tu agente real</div>
            <p style={{ fontSize: 14, color: 'var(--text)', margin: '0 0 12px', lineHeight: 1.5 }}>
              Vas a configurar tu agente con los datos de <strong>{demo.source.name}</strong>.
            </p>
            <div style={{ fontSize: 13.5, color: 'var(--muted)', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 12px', marginBottom: 12, lineHeight: 1.5 }}>
              Esto <strong style={{ color: 'var(--text)' }}>reemplazará</strong> la configuración actual
              {liveName ? <> (<strong style={{ color: 'var(--text)' }}>{liveName}</strong>)</> : ''}: nombre, descripción, tono, servicios, horario y ficha de información.
              <br />
              <span style={{ color: '#48bb78' }}>No afecta</span> a la conexión de WhatsApp/voz ni a tus claves.
            </div>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <Button variant="ghost" onClick={() => setConfirmOpen(false)} disabled={applyState === 'applying'}>Cancelar</Button>
              <Button onClick={apply} disabled={applyState === 'applying'}>
                {applyState === 'applying' ? 'Aplicando…' : 'Sí, aplicar'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
