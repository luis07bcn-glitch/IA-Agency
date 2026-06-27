'use client';

import { useState, useEffect } from 'react';
import { api, AgentConfig } from '@/lib/api';

// ── Shared primitives (same pattern as agente/page.tsx) ──────────────────────
function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 12, padding: 20, ...style }}>
      {children}
    </div>
  );
}
function Label({ children }: { children: React.ReactNode }) {
  return <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', marginBottom: 4 }}>{children}</div>;
}
function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input {...props} style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 14, background: 'var(--bg)', color: 'var(--text)', boxSizing: 'border-box', ...props.style }} />
  );
}
function Button({ children, onClick, disabled, variant = 'primary' }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean; variant?: 'primary' | 'danger' | 'ghost' }) {
  const bg = variant === 'primary' ? 'var(--primary)' : variant === 'danger' ? '#e53e3e' : 'transparent';
  const border = variant === 'ghost' ? '1px solid var(--border)' : 'none';
  return (
    <button onClick={onClick} disabled={disabled}
      style={{ padding: '9px 18px', borderRadius: 8, border, background: bg, color: variant === 'ghost' ? 'var(--text)' : '#fff', fontWeight: 600, fontSize: 14, cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.6 : 1 }}>
      {children}
    </button>
  );
}

// ── Override selector ─────────────────────────────────────────────────────────
const OVERRIDES = [
  { value: 'auto', label: 'Según horario', desc: 'El agente atiende solo en el horario configurado' },
  { value: 'agent', label: '📞 Contesta el agente', desc: 'Fuerza al agente a atender todas las llamadas ahora' },
  { value: 'staff', label: '🧑 Contesto yo', desc: 'Todas las llamadas van al teléfono del personal' },
] as const;

const DAYS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

export default function VozPage() {
  const [cfg, setCfg] = useState<AgentConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => { api.get<AgentConfig>('/config').then(setCfg); }, []);

  const save = async () => {
    if (!cfg) return;
    setSaving(true);
    const updated = await api.put<AgentConfig>('/config', {
      voiceEnabled: cfg.voiceEnabled,
      voiceOverride: cfg.voiceOverride,
      staffPhone: cfg.staffPhone ?? '',
      voiceSchedule: cfg.voiceSchedule,
    });
    setCfg(updated);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const toggleDay = (weekday: number) => {
    if (!cfg) return;
    const existing = cfg.voiceSchedule.find((d) => d.weekday === weekday);
    if (existing) {
      setCfg({ ...cfg, voiceSchedule: cfg.voiceSchedule.filter((d) => d.weekday !== weekday) });
    } else {
      setCfg({ ...cfg, voiceSchedule: [...cfg.voiceSchedule, { weekday, intervals: [{ start: '09:00', end: '21:00' }] }] });
    }
  };

  const updateInterval = (weekday: number, field: 'start' | 'end', value: string) => {
    if (!cfg) return;
    setCfg({
      ...cfg,
      voiceSchedule: cfg.voiceSchedule.map((d) =>
        d.weekday !== weekday ? d : { ...d, intervals: [{ ...d.intervals[0], [field]: value }] }
      ),
    });
  };

  if (!cfg) return <div style={{ padding: 40, color: 'var(--muted)' }}>Cargando…</div>;

  return (
    <div style={{ maxWidth: 780, margin: '0 auto', padding: '32px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontWeight: 800, fontSize: 26, margin: 0 }}>📞 Canal de Voz</h1>
          <p style={{ color: 'var(--muted)', margin: '4px 0 0', fontSize: 14 }}>
            Configura el agente que atiende las llamadas telefónicas del negocio.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {saved && <span style={{ color: 'var(--primary)', fontWeight: 600, fontSize: 14 }}>✓ Guardado</span>}
          <Button onClick={save} disabled={saving}>{saving ? 'Guardando…' : 'Guardar cambios'}</Button>
        </div>
      </div>

      {/* On/Off */}
      <Card style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div
            onClick={() => setCfg({ ...cfg, voiceEnabled: !cfg.voiceEnabled })}
            style={{
              width: 52, height: 28, borderRadius: 14, cursor: 'pointer', position: 'relative', flexShrink: 0,
              background: cfg.voiceEnabled ? 'var(--primary)' : 'var(--border)', transition: 'background 0.2s',
            }}
          >
            <div style={{
              position: 'absolute', top: 3, left: cfg.voiceEnabled ? 27 : 3,
              width: 22, height: 22, borderRadius: '50%', background: '#fff', transition: 'left 0.2s',
            }} />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>
              {cfg.voiceEnabled ? 'Canal de voz activo' : 'Canal de voz desactivado'}
            </div>
            <div style={{ fontSize: 13, color: 'var(--muted)' }}>
              {cfg.voiceEnabled ? 'El agente puede atender llamadas.' : 'Actívalo para que el agente atienda llamadas.'}
            </div>
          </div>
        </div>
      </Card>

      {cfg.voiceEnabled && (
        <>
          {/* Override instantáneo */}
          <Card style={{ marginBottom: 20 }}>
            <h3 style={{ fontWeight: 700, marginBottom: 4 }}>¿Quién contesta ahora?</h3>
            <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 14 }}>
              Interruptor instantáneo. Tiene prioridad sobre el horario configurado.
            </p>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {OVERRIDES.map(({ value, label, desc }) => (
                <div
                  key={value}
                  onClick={() => setCfg({ ...cfg, voiceOverride: value })}
                  style={{
                    flex: 1, minWidth: 160, padding: 14, borderRadius: 10, cursor: 'pointer',
                    border: cfg.voiceOverride === value ? '2px solid var(--primary)' : '1px solid var(--border)',
                    background: cfg.voiceOverride === value ? 'var(--primary)' : 'var(--card)',
                    color: cfg.voiceOverride === value ? '#fff' : 'var(--text)',
                    transition: 'all 0.15s',
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 4 }}>{label}</div>
                  <div style={{ fontSize: 12, opacity: 0.8 }}>{desc}</div>
                </div>
              ))}
            </div>
          </Card>

          {/* Teléfono personal */}
          <Card style={{ marginBottom: 20 }}>
            <h3 style={{ fontWeight: 700, marginBottom: 4 }}>Teléfono de desvío (personal)</h3>
            <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
              Cuando el agente NO deba contestar, la llamada se desvía a este número. Si está vacío, se reproduce un mensaje de aviso.
            </p>
            <Label>Número en formato internacional</Label>
            <Input
              type="tel"
              placeholder="+34600000000"
              value={cfg.staffPhone ?? ''}
              onChange={(e) => setCfg({ ...cfg, staffPhone: e.target.value })}
            />
          </Card>

          {/* Horario automático */}
          {cfg.voiceOverride === 'auto' && (
            <Card style={{ marginBottom: 20 }}>
              <h3 style={{ fontWeight: 700, marginBottom: 4 }}>Horario del agente (Mando automático)</h3>
              <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
                Marca los días en que el agente atiende llamadas y ajusta el intervalo horario por día.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[1, 2, 3, 4, 5, 6, 0].map((weekday) => {
                  const active = cfg.voiceSchedule.find((d) => d.weekday === weekday);
                  return (
                    <div key={weekday} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div
                        onClick={() => toggleDay(weekday)}
                        style={{
                          width: 40, height: 24, borderRadius: 12, cursor: 'pointer', position: 'relative', flexShrink: 0,
                          background: active ? 'var(--primary)' : 'var(--border)', transition: 'background 0.2s',
                        }}
                      >
                        <div style={{ position: 'absolute', top: 2, left: active ? 18 : 2, width: 20, height: 20, borderRadius: '50%', background: '#fff', transition: 'left 0.2s' }} />
                      </div>
                      <span style={{ width: 36, fontWeight: 600, fontSize: 13 }}>{DAYS[weekday]}</span>
                      {active && (
                        <>
                          <Input type="time" value={active.intervals[0]?.start ?? '09:00'}
                            onChange={(e) => updateInterval(weekday, 'start', e.target.value)}
                            style={{ width: 110 }} />
                          <span style={{ color: 'var(--muted)', fontSize: 13 }}>a</span>
                          <Input type="time" value={active.intervals[0]?.end ?? '21:00'}
                            onChange={(e) => updateInterval(weekday, 'end', e.target.value)}
                            style={{ width: 110 }} />
                        </>
                      )}
                      {!active && <span style={{ color: 'var(--muted)', fontSize: 13 }}>Desactivado</span>}
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* Instrucciones de conexión */}
          <Card style={{ borderLeft: '4px solid var(--primary)' }}>
            <h3 style={{ fontWeight: 700, marginBottom: 8 }}>Conectar con Twilio</h3>
            <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
              Para que el agente atienda llamadas reales, añade estas 3 variables al archivo <code>.env</code> del servidor:
            </p>
            <pre style={{ background: 'var(--bg)', borderRadius: 8, padding: 14, fontSize: 12, overflowX: 'auto' }}>
{`TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+34900000000
PUBLIC_URL=https://api.tudominio.com`}
            </pre>
            <p style={{ fontSize: 13, color: 'var(--muted)', marginTop: 10 }}>
              En Twilio, configura el número de teléfono para que el webhook de voz apunte a:<br />
              <code style={{ color: 'var(--primary)' }}>POST https://api.tudominio.com/api/voice/incoming</code>
            </p>
          </Card>
        </>
      )}
    </div>
  );
}
