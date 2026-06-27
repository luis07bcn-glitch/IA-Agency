'use client';

import { useCallback, useEffect, useState } from 'react';
import { api, Appointment, Patient } from '@/lib/api';
import { useEvents } from '@/lib/useEvents';
import { Button, Card, Input, Label, PageTitle, StatusBadge, TextArea, fmtDateTime } from '../ui';

const EMPTY = { name: '', phone: '', email: '', notes: '' };

export default function PacientesPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Patient | null>(null);
  const [form, setForm] = useState(EMPTY);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const load = useCallback(() => {
    api
      .get<Patient[]>(`/patients${search ? `?search=${encodeURIComponent(search)}` : ''}`)
      .then(setPatients)
      .catch(() => {});
  }, [search]);

  useEffect(() => load(), [load]);
  useEvents(['patient.changed', 'appointment.changed'], () => {
    load();
    if (selected) api.get<Patient>(`/patients/${selected.id}`).then(setSelected).catch(() => {});
  });

  const openCreate = () => {
    setForm(EMPTY);
    setEditingId(null);
    setShowForm(true);
  };

  const openEdit = (p: Patient) => {
    setForm({ name: p.name, phone: p.phone, email: p.email ?? '', notes: p.notes ?? '' });
    setEditingId(p.id);
    setShowForm(true);
  };

  const submit = async () => {
    const body = { ...form, email: form.email || undefined, notes: form.notes || undefined };
    if (editingId) await api.put(`/patients/${editingId}`, body);
    else await api.post('/patients', body);
    setShowForm(false);
    load();
  };

  const remove = async (id: string) => {
    if (!confirm('¿Borrar este paciente y sus citas?')) return;
    await api.del(`/patients/${id}`);
    if (selected?.id === id) setSelected(null);
    load();
  };

  const openDetail = (p: Patient) => {
    api.get<Patient>(`/patients/${p.id}`).then(setSelected).catch(() => {});
  };

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle>Pacientes</PageTitle>
        <Button onClick={openCreate}>+ Nuevo paciente</Button>
      </div>

      <div style={{ marginBottom: 16, maxWidth: 360 }}>
        <Input
          placeholder="Buscar por nombre, teléfono o email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
        <Card style={{ flex: 1 }}>
          {patients.length === 0 && <p style={{ color: 'var(--muted)' }}>No hay pacientes.</p>}
          {patients.map((p) => (
            <div
              key={p.id}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '10px 0',
                borderBottom: '1px solid var(--border)',
              }}
            >
              <div onClick={() => openDetail(p)} style={{ cursor: 'pointer' }}>
                <div style={{ fontWeight: 600 }}>{p.name}</div>
                <div style={{ fontSize: 13, color: 'var(--muted)' }}>{p.phone}</div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <Button variant="ghost" onClick={() => openEdit(p)}>Editar</Button>
                <Button variant="danger" onClick={() => remove(p.id)}>Borrar</Button>
              </div>
            </div>
          ))}
        </Card>

        {selected && (
          <Card style={{ width: 360 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <h3 style={{ fontWeight: 700, fontSize: 17 }}>{selected.name}</h3>
              <span onClick={() => setSelected(null)} style={{ cursor: 'pointer', color: 'var(--muted)' }}>✕</span>
            </div>
            <p style={{ fontSize: 14, color: 'var(--muted)', margin: '4px 0' }}>{selected.phone}</p>
            {selected.email && <p style={{ fontSize: 14, color: 'var(--muted)' }}>{selected.email}</p>}
            {selected.notes && (
              <p style={{ fontSize: 14, marginTop: 8, background: '#f9fafb', padding: 10, borderRadius: 8 }}>
                {selected.notes}
              </p>
            )}
            <h4 style={{ fontWeight: 700, fontSize: 14, margin: '16px 0 8px' }}>Citas</h4>
            {(selected.appointments ?? []).length === 0 && (
              <p style={{ color: 'var(--muted)', fontSize: 13 }}>Sin citas.</p>
            )}
            {(selected.appointments ?? []).map((a: Appointment) => (
              <div key={a.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>{a.serviceName}</span>
                  <StatusBadge status={a.status} />
                </div>
                <div style={{ fontSize: 13, color: 'var(--muted)' }}>{fmtDateTime(a.startsAt)}</div>
              </div>
            ))}
          </Card>
        )}
      </div>

      {showForm && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
          }}
          onClick={() => setShowForm(false)}
        >
          <div onClick={(e) => e.stopPropagation()} style={{ width: 420 }}>
            <Card>
              <h3 style={{ fontWeight: 700, fontSize: 18, marginBottom: 14 }}>
                {editingId ? 'Editar paciente' : 'Nuevo paciente'}
              </h3>
              <div style={{ marginBottom: 12 }}>
                <Label>Nombre</Label>
                <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div style={{ marginBottom: 12 }}>
                <Label>Teléfono (WhatsApp)</Label>
                <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="+34600111222" />
              </div>
              <div style={{ marginBottom: 12 }}>
                <Label>Email</Label>
                <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </div>
              <div style={{ marginBottom: 16 }}>
                <Label>Notas</Label>
                <TextArea rows={3} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <Button variant="ghost" onClick={() => setShowForm(false)}>Cancelar</Button>
                <Button onClick={submit} disabled={!form.name || !form.phone}>Guardar</Button>
              </div>
            </Card>
          </div>
        </div>
      )}
    </>
  );
}
