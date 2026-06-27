'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, AgentConfig, RoiMetrics } from '@/lib/api';

function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 12, padding: 20, ...style }}>
      {children}
    </div>
  );
}
function Button({ children, onClick, disabled, variant = 'primary' }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean; variant?: 'primary' | 'ghost' }) {
  return (
    <button onClick={onClick} disabled={disabled}
      style={{ padding: '9px 16px', borderRadius: 8, border: variant === 'ghost' ? '1px solid var(--border)' : 'none', background: variant === 'ghost' ? 'transparent' : 'var(--primary)', color: variant === 'ghost' ? 'var(--text)' : '#fff', fontWeight: 600, fontSize: 14, cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.6 : 1 }}>
      {children}
    </button>
  );
}

function Delta({ value }: { value: number | null }) {
  if (value == null) return null;
  const up = value >= 0;
  return (
    <span style={{ fontSize: 12, fontWeight: 700, color: up ? '#48bb78' : '#e53e3e', marginLeft: 8 }}>
      {up ? '▲' : '▼'} {Math.abs(value)}%
    </span>
  );
}

function BigStat({ icon, value, label, delta, highlight }: { icon: string; value: string; label: string; delta?: number | null; highlight?: boolean }) {
  return (
    <Card style={highlight ? { borderColor: 'var(--primary)', borderWidth: 2 } : undefined}>
      <div style={{ fontSize: 24, marginBottom: 6 }}>{icon}</div>
      <div style={{ display: 'flex', alignItems: 'baseline' }}>
        <span style={{ fontSize: 30, fontWeight: 800, color: highlight ? 'var(--primary)' : 'var(--text)' }}>{value}</span>
        {delta !== undefined && <Delta value={delta} />}
      </div>
      <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 4 }}>{label}</div>
    </Card>
  );
}

const PERIODS = [
  { days: 7, label: '7 días' },
  { days: 30, label: '30 días' },
  { days: 90, label: '90 días' },
];

export default function ResultadosPage() {
  const [days, setDays] = useState(30);
  const [roi, setRoi] = useState<RoiMetrics | null>(null);
  const [cfg, setCfg] = useState<AgentConfig | null>(null);
  const [savingTicket, setSavingTicket] = useState(false);
  const [digestMsg, setDigestMsg] = useState('');

  const load = useCallback(async () => {
    const [r, c] = await Promise.all([
      api.get<RoiMetrics>(`/metrics/roi?days=${days}`),
      api.get<AgentConfig>('/config'),
    ]);
    setRoi(r);
    setCfg(c);
  }, [days]);

  useEffect(() => { load(); }, [load]);

  const saveTicket = async (value: number) => {
    setSavingTicket(true);
    await api.put<AgentConfig>('/config', { avgTicket: value });
    await load();
    setSavingTicket(false);
  };

  const toggleDigest = async () => {
    if (!cfg) return;
    const updated = await api.put<AgentConfig>('/config', { dailyDigestEnabled: !cfg.dailyDigestEnabled });
    setCfg(updated);
  };

  const saveOwnerPhone = async (phone: string) => {
    const updated = await api.put<AgentConfig>('/config', { ownerPhone: phone });
    setCfg(updated);
  };

  const sendTest = async () => {
    setDigestMsg('Enviando…');
    try {
      const r = await api.post<{ ok: boolean; sentTo: string }>('/metrics/digest-test', {});
      setDigestMsg(`✓ Enviado a ${r.sentTo}`);
    } catch (e) {
      setDigestMsg(`✗ ${e instanceof Error ? e.message : 'Error'} (¿WhatsApp configurado?)`);
    }
    setTimeout(() => setDigestMsg(''), 5000);
  };

  if (!roi || !cfg) return <div style={{ padding: 40, color: 'var(--muted)' }}>Cargando…</div>;

  const revenue = roi.estimatedRevenue;

  return (
    <div style={{ maxWidth: 920, margin: '0 auto', padding: '32px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontWeight: 800, fontSize: 26, margin: 0 }}>📈 Resultados del agente</h1>
          <p style={{ color: 'var(--muted)', margin: '4px 0 0', fontSize: 14 }}>
            Lo que el asistente está haciendo por tu negocio.
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

      {/* Hero: ingresos estimados */}
      <Card style={{ margin: '20px 0', background: 'linear-gradient(135deg, var(--primary), #6b46c1)', border: 'none', color: '#fff' }}>
        <div style={{ fontSize: 14, opacity: 0.9, marginBottom: 6 }}>💰 Ingresos estimados generados por el agente</div>
        {revenue != null ? (
          <div style={{ fontSize: 44, fontWeight: 800 }}>{revenue.toLocaleString('es-ES')} €</div>
        ) : (
          <div style={{ fontSize: 18, fontWeight: 600, opacity: 0.95 }}>
            Configura el ticket medio abajo para ver la estimación →
          </div>
        )}
        <div style={{ fontSize: 13, opacity: 0.85, marginTop: 6 }}>
          {roi.appointmentsByAgent} cita(s) reservadas por el agente en los últimos {roi.periodDays} días
        </div>
      </Card>

      {/* Stats grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14, marginBottom: 20 }}>
        <BigStat icon="🤖" value={String(roi.appointmentsByAgent)} label="Citas reservadas por el agente" delta={roi.deltaAppointmentsByAgent} highlight />
        <BigStat icon="💬" value={String(roi.messagesHandled)} label="Mensajes atendidos" delta={roi.deltaMessages} />
        <BigStat icon="👥" value={String(roi.whatsappConversations)} label="Conversaciones de WhatsApp" />
        <BigStat icon="📅" value={String(roi.appointmentsTotal)} label="Citas totales creadas" />
        <BigStat icon="✅" value={String(roi.completed)} label="Citas completadas" />
        <BigStat icon="⚠️" value={`${Math.round(roi.noShowRate * 100)}%`} label={`Tasa de ausencias (${roi.noShow})`} />
      </div>

      {/* Ticket medio */}
      <Card style={{ marginBottom: 20 }}>
        <h3 style={{ fontWeight: 700, marginBottom: 4 }}>Ticket medio</h3>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
          Valor medio de una cita/reserva. Sirve para estimar los ingresos generados. Solo tú lo ves.
        </p>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <input
            type="number" min={0}
            defaultValue={cfg.avgTicket ?? ''}
            placeholder="Ej: 45"
            id="ticket-input"
            style={{ width: 120, padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 14, background: 'var(--bg)', color: 'var(--text)' }}
          />
          <span style={{ color: 'var(--muted)' }}>€</span>
          <Button disabled={savingTicket} onClick={() => {
            const el = document.getElementById('ticket-input') as HTMLInputElement;
            saveTicket(Number(el.value) || 0);
          }}>
            {savingTicket ? 'Guardando…' : 'Guardar'}
          </Button>
        </div>
      </Card>

      {/* Resumen diario por WhatsApp */}
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 14 }}>
          <div onClick={toggleDigest}
            style={{ width: 52, height: 28, borderRadius: 14, cursor: 'pointer', position: 'relative', flexShrink: 0, background: cfg.dailyDigestEnabled ? 'var(--primary)' : 'var(--border)' }}>
            <div style={{ position: 'absolute', top: 3, left: cfg.dailyDigestEnabled ? 27 : 3, width: 22, height: 22, borderRadius: '50%', background: '#fff', transition: 'left 0.2s' }} />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>Resumen diario por WhatsApp</div>
            <div style={{ fontSize: 13, color: 'var(--muted)' }}>Cada mañana a las 8:00, el dueño recibe un resumen del día y de los resultados.</div>
          </div>
        </div>

        {cfg.dailyDigestEnabled && (
          <div style={{ paddingTop: 14, borderTop: '1px solid var(--border)' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', marginBottom: 4 }}>Teléfono del dueño (WhatsApp)</div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <input
                type="tel"
                defaultValue={cfg.ownerPhone ?? ''}
                placeholder="+34600000000"
                id="owner-phone"
                style={{ flex: 1, minWidth: 180, padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 14, background: 'var(--bg)', color: 'var(--text)' }}
              />
              <Button variant="ghost" onClick={() => {
                const el = document.getElementById('owner-phone') as HTMLInputElement;
                saveOwnerPhone(el.value);
              }}>Guardar número</Button>
              <Button onClick={sendTest}>Enviar prueba ahora</Button>
            </div>
            {digestMsg && <p style={{ fontSize: 13, marginTop: 8, color: digestMsg.startsWith('✓') ? '#48bb78' : 'var(--muted)' }}>{digestMsg}</p>}
          </div>
        )}
      </Card>
    </div>
  );
}
