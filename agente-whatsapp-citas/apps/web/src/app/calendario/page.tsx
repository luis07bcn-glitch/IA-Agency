'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { AgentConfig, Appointment, Patient, api } from '@/lib/api';
import { useEvents } from '@/lib/useEvents';
import { Button, Card, Label, PageTitle, StatusBadge } from '../ui';

type View = 'month' | 'week';
const DAY_MS = 24 * 3600 * 1000;
const WEEKDAYS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

function startOfWeek(d: Date): Date {
  const day = (d.getDay() + 6) % 7; // Monday = 0
  const r = new Date(d);
  r.setHours(0, 0, 0, 0);
  r.setDate(r.getDate() - day);
  return r;
}
function startOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}
function ymd(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
function hhmm(iso: string): string {
  return new Intl.DateTimeFormat('es-ES', { hour: '2-digit', minute: '2-digit' }).format(new Date(iso));
}

interface Slot { startsAt: string; label: string }

export default function CalendarioPage() {
  const [view, setView] = useState<View>('week');
  const [cursor, setCursor] = useState(() => new Date());
  const [appts, setAppts] = useState<Appointment[]>([]);
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);

  // Create modal state
  const [modalDate, setModalDate] = useState<string | null>(null);
  const [form, setForm] = useState({ patientId: '', service: '' });
  const [slots, setSlots] = useState<Slot[]>([]);
  const [chosenSlot, setChosenSlot] = useState<string>('');

  const range = useMemo(() => {
    if (view === 'week') {
      const from = startOfWeek(cursor);
      const to = new Date(from.getTime() + 7 * DAY_MS);
      return { from, to };
    }
    const first = startOfMonth(cursor);
    const from = startOfWeek(first);
    const to = new Date(from.getTime() + 42 * DAY_MS);
    return { from, to };
  }, [view, cursor]);

  const load = useCallback(() => {
    api
      .get<Appointment[]>(`/appointments?from=${range.from.toISOString()}&to=${range.to.toISOString()}`)
      .then(setAppts)
      .catch(() => {});
  }, [range.from, range.to]);

  useEffect(() => load(), [load]);
  useEffect(() => {
    api.get<AgentConfig>('/config').then(setConfig).catch(() => {});
    api.get<Patient[]>('/patients').then(setPatients).catch(() => {});
  }, []);
  useEvents(['appointment.changed'], () => load());

  const byDay = useMemo(() => {
    const map: Record<string, Appointment[]> = {};
    for (const a of appts) {
      const key = ymd(new Date(a.startsAt));
      (map[key] ??= []).push(a);
    }
    for (const k of Object.keys(map)) map[k].sort((a, b) => a.startsAt.localeCompare(b.startsAt));
    return map;
  }, [appts]);

  const move = (dir: number) => {
    const d = new Date(cursor);
    if (view === 'week') d.setDate(d.getDate() + dir * 7);
    else d.setMonth(d.getMonth() + dir);
    setCursor(d);
  };

  const openModal = (dateKey: string) => {
    setModalDate(dateKey);
    setForm({ patientId: patients[0]?.id ?? '', service: config?.services[0]?.name ?? '' });
    setSlots([]);
    setChosenSlot('');
  };

  const loadSlots = useCallback(() => {
    if (!modalDate || !form.service) return;
    api
      .get<Slot[]>(`/appointments/availability?service=${encodeURIComponent(form.service)}&date=${modalDate}`)
      .then(setSlots)
      .catch(() => setSlots([]));
  }, [modalDate, form.service]);

  useEffect(() => loadSlots(), [loadSlots]);

  const book = async () => {
    if (!form.patientId || !form.service || !chosenSlot) return;
    await api.post('/appointments', {
      patientId: form.patientId,
      serviceName: form.service,
      startsAt: chosenSlot,
    });
    setModalDate(null);
    load();
  };

  const cancel = async (id: string) => {
    if (!confirm('¿Cancelar esta cita?')) return;
    await api.put(`/appointments/${id}`, { status: 'cancelled' });
    load();
  };

  // Build day cells
  const cells: Date[] = [];
  const total = view === 'week' ? 7 : 42;
  for (let i = 0; i < total; i++) cells.push(new Date(range.from.getTime() + i * DAY_MS));

  const title =
    view === 'week'
      ? `Semana del ${range.from.toLocaleDateString('es-ES', { day: 'numeric', month: 'long' })}`
      : cursor.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle>Calendario</PageTitle>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button variant={view === 'week' ? 'primary' : 'ghost'} onClick={() => setView('week')}>Semana</Button>
          <Button variant={view === 'month' ? 'primary' : 'ghost'} onClick={() => setView('month')}>Mes</Button>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <Button variant="ghost" onClick={() => move(-1)}>‹ Anterior</Button>
        <strong style={{ textTransform: 'capitalize' }}>{title}</strong>
        <Button variant="ghost" onClick={() => move(1)}>Siguiente ›</Button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 8 }}>
        {WEEKDAYS.map((d) => (
          <div key={d} style={{ textAlign: 'center', fontSize: 12, fontWeight: 700, color: 'var(--muted)' }}>{d}</div>
        ))}
        {cells.map((day) => {
          const key = ymd(day);
          const items = byDay[key] ?? [];
          const isToday = key === ymd(new Date());
          const dimmed = view === 'month' && day.getMonth() !== cursor.getMonth();
          return (
            <div
              key={key}
              onClick={() => openModal(key)}
              style={{
                background: 'var(--card)',
                border: isToday ? '2px solid var(--primary)' : '1px solid var(--border)',
                borderRadius: 10,
                padding: 8,
                minHeight: view === 'week' ? 220 : 96,
                opacity: dimmed ? 0.45 : 1,
                cursor: 'pointer',
              }}
            >
              <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 6 }}>{day.getDate()}</div>
              {items.slice(0, view === 'week' ? 20 : 3).map((a) => (
                <div
                  key={a.id}
                  onClick={(e) => { e.stopPropagation(); if (a.status === 'scheduled') cancel(a.id); }}
                  title={`${a.serviceName} — ${a.patient?.name ?? ''}`}
                  style={{
                    fontSize: 11,
                    background: a.status === 'cancelled' ? '#f3f4f6' : '#ccfbf1',
                    color: a.status === 'cancelled' ? '#9ca3af' : '#0f766e',
                    borderRadius: 6,
                    padding: '2px 6px',
                    marginBottom: 3,
                    textDecoration: a.status === 'cancelled' ? 'line-through' : 'none',
                    overflow: 'hidden',
                    whiteSpace: 'nowrap',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {hhmm(a.startsAt)} {a.patient?.name?.split(' ')[0] ?? ''} {a.source === 'agent' ? '🤖' : ''}
                </div>
              ))}
              {view === 'month' && items.length > 3 && (
                <div style={{ fontSize: 10, color: 'var(--muted)' }}>+{items.length - 3} más</div>
              )}
            </div>
          );
        })}
      </div>

      <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 10 }}>
        Toca un día para reservar. Toca una cita programada para cancelarla. 🤖 = reservada por el agente.
      </p>

      {modalDate && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}
          onClick={() => setModalDate(null)}
        >
          <div onClick={(e) => e.stopPropagation()} style={{ width: 440 }}>
            <Card>
              <h3 style={{ fontWeight: 700, fontSize: 18, marginBottom: 14 }}>Nueva cita — {modalDate}</h3>
              <div style={{ marginBottom: 12 }}>
                <Label>Paciente</Label>
                <select
                  value={form.patientId}
                  onChange={(e) => setForm({ ...form, patientId: e.target.value })}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)' }}
                >
                  <option value="">— Selecciona —</option>
                  {patients.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.phone})</option>)}
                </select>
              </div>
              <div style={{ marginBottom: 12 }}>
                <Label>Servicio</Label>
                <select
                  value={form.service}
                  onChange={(e) => { setForm({ ...form, service: e.target.value }); setChosenSlot(''); }}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)' }}
                >
                  {config?.services.map((s) => <option key={s.name} value={s.name}>{s.name} ({s.durationMin} min)</option>)}
                </select>
              </div>
              <div style={{ marginBottom: 16 }}>
                <Label>Hueco disponible</Label>
                {slots.length === 0 && <p style={{ fontSize: 13, color: 'var(--muted)' }}>No hay huecos libres ese día.</p>}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {slots.map((s) => (
                    <button
                      key={s.startsAt}
                      onClick={() => setChosenSlot(s.startsAt)}
                      style={{
                        padding: '6px 12px',
                        borderRadius: 8,
                        border: '1px solid var(--border)',
                        background: chosenSlot === s.startsAt ? 'var(--primary)' : '#fff',
                        color: chosenSlot === s.startsAt ? '#fff' : 'var(--text)',
                        cursor: 'pointer',
                        fontSize: 13,
                      }}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <Button variant="ghost" onClick={() => setModalDate(null)}>Cancelar</Button>
                <Button onClick={book} disabled={!form.patientId || !chosenSlot}>Reservar</Button>
              </div>
            </Card>
          </div>
        </div>
      )}
    </>
  );
}
