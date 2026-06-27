'use client';

import { useEffect, useState } from 'react';
import { AgentConfig, api } from '@/lib/api';
import { Button, Card, Input, Label, PageTitle, TextArea } from '../ui';
import { Playground } from './playground';

const DAY_NAMES = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
const ORDER = [1, 2, 3, 4, 5, 6, 0]; // Mon..Sun

interface ModelOption { id: string; label: string }

function ExternalCalendarCard({ url, onSave }: { url: string; onSave: (url: string) => Promise<void> }) {
  const [value, setValue] = useState(url);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const save = async () => {
    setSaving(true);
    await onSave(value.trim());
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <Card style={{ marginTop: 20 }}>
      <h3 style={{ fontWeight: 700, marginBottom: 8 }}>Calendario externo</h3>
      <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 4 }}>
        Conecta con TheFork, CoverManager, Google Calendar u otro sistema de reservas para evitar solapamientos.
        El agente consultará automáticamente este calendario antes de ofrecer huecos.
      </p>
      <details style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 14, cursor: 'pointer' }}>
        <summary style={{ fontWeight: 600 }}>¿Cómo obtengo la URL? (haz clic para ver)</summary>
        <div style={{ marginTop: 8, lineHeight: 1.7 }}>
          <strong>Google Calendar:</strong> Configuración del calendario → «Dirección secreta en formato iCal» → copiar URL<br />
          <strong>TheFork:</strong> Panel → Reservas → Exportar → iCal → copiar enlace<br />
          <strong>Outlook / Office 365:</strong> Calendario → Compartir → «Obtener un vínculo» → formato iCal<br />
          <strong>Otros sistemas:</strong> busca «exportar iCal» o «sincronizar calendario» en su configuración
        </div>
      </details>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <input
          type="url"
          placeholder="https://calendar.google.com/calendar/ical/..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          style={{ flex: 1, padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13 }}
        />
        <Button onClick={save} disabled={saving}>
          {saving ? 'Guardando…' : 'Guardar'}
        </Button>
        {saved && <span style={{ color: 'var(--primary)', fontSize: 13, fontWeight: 600 }}>✓</span>}
      </div>
      {value && (
        <p style={{ fontSize: 12, color: 'var(--primary)', marginTop: 6 }}>
          ✓ Calendario conectado — el agente evitará huecos ocupados
        </p>
      )}
    </Card>
  );
}

function KnowledgeBaseCard() {
  const [status, setStatus] = useState<'idle' | 'uploading' | 'ok' | 'error'>('idle');
  const [info, setInfo] = useState<string>('');

  const upload = async (file: File) => {
    setStatus('uploading');
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3001'}/api/config/knowledge`, {
        method: 'POST',
        headers: { 'Content-Type': file.type || 'application/octet-stream' },
        body: file,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json() as { characters: number };
      setInfo(`${data.characters.toLocaleString()} caracteres cargados`);
      setStatus('ok');
    } catch (e) {
      setInfo(e instanceof Error ? e.message : 'Error desconocido');
      setStatus('error');
    }
  };

  const clear = async () => {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3001'}/api/config/knowledge`, { method: 'DELETE' });
    setStatus('idle');
    setInfo('');
  };

  return (
    <Card style={{ marginTop: 20 }}>
      <h3 style={{ fontWeight: 700, marginBottom: 8 }}>Base de conocimiento</h3>
      <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 14 }}>
        Sube un PDF o texto con información del centro (precios, protocolos, FAQs…). El agente lo usará para responder preguntas.
      </p>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <label style={{
          padding: '8px 18px', borderRadius: 8, background: 'var(--primary)', color: '#fff',
          fontWeight: 600, cursor: 'pointer', fontSize: 14,
        }}>
          {status === 'uploading' ? 'Procesando…' : '📄 Subir PDF o texto'}
          <input
            type="file"
            accept=".pdf,.txt,.md"
            style={{ display: 'none' }}
            disabled={status === 'uploading'}
            onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(f); e.target.value = ''; }}
          />
        </label>
        {(status === 'ok' || status === 'error') && (
          <button onClick={clear} style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 14px', cursor: 'pointer', fontSize: 13 }}>
            Eliminar
          </button>
        )}
        {info && (
          <span style={{ fontSize: 13, color: status === 'error' ? '#b91c1c' : 'var(--primary)', fontWeight: 600 }}>
            {status === 'ok' ? '✓ ' : '✗ '}{info}
          </span>
        )}
      </div>
    </Card>
  );
}

export default function AgentePage() {
  const [cfg, setCfg] = useState<AgentConfig | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [models, setModels] = useState<ModelOption[]>([]);
  const [showAll, setShowAll] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get<AgentConfig>('/config').then(setCfg).catch(() => {});
    api.get<{ models: ModelOption[] }>('/config/models').then((r) => setModels(r.models)).catch(() => {});
  }, []);

  const loadAllModels = async () => {
    setShowAll(true);
    const r = await api.get<{ models: ModelOption[] }>('/config/models?all=true');
    setModels(r.models);
  };

  const save = async () => {
    if (!cfg) return;
    const body: any = {
      centerName: cfg.centerName,
      description: cfg.description,
      tone: cfg.tone,
      timezone: cfg.timezone,
      enabled: cfg.enabled,
      services: cfg.services,
      schedule: cfg.schedule,
      agentModel: cfg.agentModel,
    };
    if (apiKey.trim()) body.openrouterApiKey = apiKey.trim();
    const updated = await api.put<AgentConfig>('/config', body);
    setCfg(updated);
    setApiKey('');
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  if (!cfg) return <PageTitle>Cargando…</PageTitle>;

  const setDay = (weekday: number, intervals: { start: string; end: string }[]) => {
    const schedule = [...cfg.schedule.filter((d) => d.weekday !== weekday), { weekday, intervals }];
    setCfg({ ...cfg, schedule });
  };
  const dayIntervals = (weekday: number) =>
    cfg.schedule.find((d) => d.weekday === weekday)?.intervals ?? [];

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle>Agente</PageTitle>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {saved && <span style={{ color: 'var(--primary)', fontSize: 13 }}>✓ Guardado</span>}
          <Button onClick={save}>Guardar cambios</Button>
        </div>
      </div>

      {/* Canales activos — resumen rápido con enlace a cada sección */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        {[
          { href: '/whatsapp', icon: '💬', label: 'WhatsApp', active: cfg.enabled, color: '#25D366' },
          { href: '/voz', icon: '📞', label: 'Voz', active: cfg.voiceEnabled, color: 'var(--primary)' },
        ].map(({ href, icon, label, active, color }) => (
          <a key={href} href={href} style={{ flex: 1, minWidth: 180, textDecoration: 'none' }}>
            <div style={{ border: `1px solid ${active ? color : 'var(--border)'}`, borderRadius: 10, padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', background: 'var(--card)' }}>
              <span style={{ fontSize: 22 }}>{icon}</span>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)' }}>{label}</div>
                <div style={{ fontSize: 12, fontWeight: 600, color: active ? color : 'var(--muted)' }}>{active ? 'Activo' : 'Desactivado'} · Ver ajustes →</div>
              </div>
            </div>
          </a>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, alignItems: 'start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Persona */}
          <Card>
            <h3 style={{ fontWeight: 700, marginBottom: 12 }}>Persona del centro</h3>
            <div style={{ marginBottom: 12 }}>
              <Label>Nombre del centro</Label>
              <Input value={cfg.centerName} onChange={(e) => setCfg({ ...cfg, centerName: e.target.value })} />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Label>Descripción</Label>
              <TextArea rows={3} value={cfg.description} onChange={(e) => setCfg({ ...cfg, description: e.target.value })} />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <Label>Tono</Label>
                <Input value={cfg.tone} onChange={(e) => setCfg({ ...cfg, tone: e.target.value })} />
              </div>
              <div style={{ flex: 1 }}>
                <Label>Zona horaria</Label>
                <Input value={cfg.timezone} onChange={(e) => setCfg({ ...cfg, timezone: e.target.value })} />
              </div>
            </div>
          </Card>

          {/* Modelo IA */}
          <Card>
            <h3 style={{ fontWeight: 700, marginBottom: 12 }}>Modelo de IA (OpenRouter)</h3>
            <div style={{ marginBottom: 12 }}>
              <Label>API key de OpenRouter</Label>
              <Input
                type="password"
                placeholder={cfg.hasOpenrouterApiKey ? '•••••••• (ya configurada, déjalo vacío para no cambiarla)' : 'Pega aquí tu API key'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
              <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
                {cfg.hasOpenrouterApiKey ? 'Hay una API key guardada.' : 'Aún no hay API key configurada.'}
              </p>
            </div>
            <div>
              <Label>Modelo</Label>
              <select
                value={cfg.agentModel}
                onChange={(e) => setCfg({ ...cfg, agentModel: e.target.value })}
                style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)' }}
              >
                {models.find((m) => m.id === cfg.agentModel) ? null : (
                  <option value={cfg.agentModel}>{cfg.agentModel}</option>
                )}
                {models.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
              </select>
              {!showAll && (
                <button onClick={loadAllModels} style={{ marginTop: 8, background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: 13, fontWeight: 600 }}>
                  Ver todos los modelos →
                </button>
              )}
            </div>
          </Card>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Servicios */}
          <Card>
            <h3 style={{ fontWeight: 700, marginBottom: 12 }}>Servicios</h3>
            {cfg.services.map((s, i) => (
              <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                <Input value={s.name} onChange={(e) => {
                  const services = [...cfg.services];
                  services[i] = { ...s, name: e.target.value };
                  setCfg({ ...cfg, services });
                }} />
                <Input type="number" value={s.durationMin} style={{ width: 90 }} onChange={(e) => {
                  const services = [...cfg.services];
                  services[i] = { ...s, durationMin: Number(e.target.value) };
                  setCfg({ ...cfg, services });
                }} />
                <Button variant="danger" onClick={() => setCfg({ ...cfg, services: cfg.services.filter((_, j) => j !== i) })}>✕</Button>
              </div>
            ))}
            <Button variant="ghost" onClick={() => setCfg({ ...cfg, services: [...cfg.services, { name: 'Nuevo servicio', durationMin: 45 }] })}>
              + Añadir servicio
            </Button>
          </Card>

          {/* Horarios */}
          <Card>
            <h3 style={{ fontWeight: 700, marginBottom: 12 }}>Horarios de atención</h3>
            {ORDER.map((wd) => {
              const intervals = dayIntervals(wd);
              return (
                <div key={wd} style={{ marginBottom: 10 }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>{DAY_NAMES[wd]}</div>
                  {intervals.length === 0 && <span style={{ fontSize: 13, color: 'var(--muted)' }}>Cerrado</span>}
                  {intervals.map((iv, idx) => (
                    <div key={idx} style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 4 }}>
                      <Input type="time" value={iv.start} style={{ width: 120 }} onChange={(e) => {
                        const next = [...intervals]; next[idx] = { ...iv, start: e.target.value }; setDay(wd, next);
                      }} />
                      <span>–</span>
                      <Input type="time" value={iv.end} style={{ width: 120 }} onChange={(e) => {
                        const next = [...intervals]; next[idx] = { ...iv, end: e.target.value }; setDay(wd, next);
                      }} />
                      <Button variant="danger" onClick={() => setDay(wd, intervals.filter((_, j) => j !== idx))}>✕</Button>
                    </div>
                  ))}
                  <button onClick={() => setDay(wd, [...intervals, { start: '09:00', end: '14:00' }])} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>
                    + franja
                  </button>
                </div>
              );
            })}
          </Card>
        </div>
      </div>

      {/* Calendario externo */}
      {cfg && <ExternalCalendarCard url={cfg.externalCalendarUrl ?? ''} onSave={async (url) => {
        const updated = await api.put<AgentConfig>('/config', { externalCalendarUrl: url });
        setCfg(updated);
      }} />}

      {/* Base de conocimiento */}
      <KnowledgeBaseCard />

      <h2 style={{ fontSize: 18, fontWeight: 700, margin: '28px 0 12px' }}>Playground</h2>
      <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
        Chatea con el agente desde aquí, sin WhatsApp, para probar cómo responde.
      </p>
      <Playground />
    </>
  );
}
