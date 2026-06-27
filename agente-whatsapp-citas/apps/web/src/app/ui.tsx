'use client';

import React from 'react';

// Small shared UI primitives so pages stay readable. Inline styles keep this
// dependency-free; Tailwind classes also work if you prefer.

export function Card({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <div
      style={{
        background: 'var(--card)',
        border: '1px solid var(--border)',
        borderRadius: 12,
        padding: 18,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

export function PageTitle({ children }: { children: React.ReactNode }) {
  return (
    <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 18 }}>{children}</h1>
  );
}

export function Button({
  children,
  onClick,
  variant = 'primary',
  type = 'button',
  disabled,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'ghost' | 'danger';
  type?: 'button' | 'submit';
  disabled?: boolean;
}) {
  const styles: Record<string, React.CSSProperties> = {
    primary: { background: 'var(--primary)', color: '#fff', border: 'none' },
    ghost: { background: '#fff', color: 'var(--text)', border: '1px solid var(--border)' },
    danger: { background: '#fee2e2', color: '#b91c1c', border: 'none' },
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      style={{
        ...styles[variant],
        padding: '9px 16px',
        borderRadius: 8,
        cursor: disabled ? 'not-allowed' : 'pointer',
        fontWeight: 600,
        fontSize: 14,
        opacity: disabled ? 0.6 : 1,
      }}
    >
      {children}
    </button>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      style={{
        width: '100%',
        padding: '9px 12px',
        borderRadius: 8,
        border: '1px solid var(--border)',
        fontSize: 14,
        ...props.style,
      }}
    />
  );
}

export function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      style={{
        width: '100%',
        padding: '9px 12px',
        borderRadius: 8,
        border: '1px solid var(--border)',
        fontSize: 14,
        fontFamily: 'inherit',
        ...props.style,
      }}
    />
  );
}

export function Label({ children }: { children: React.ReactNode }) {
  return (
    <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--muted)' }}>
      {children}
    </label>
  );
}

const STATUS_LABELS: Record<string, { text: string; color: string; bg: string }> = {
  scheduled: { text: 'Programada', color: '#0f766e', bg: '#ccfbf1' },
  completed: { text: 'Completada', color: '#3730a3', bg: '#e0e7ff' },
  cancelled: { text: 'Cancelada', color: '#9ca3af', bg: '#f3f4f6' },
  no_show: { text: 'No asistió', color: '#b91c1c', bg: '#fee2e2' },
};

export function StatusBadge({ status }: { status: string }) {
  const s = STATUS_LABELS[status] ?? STATUS_LABELS.scheduled;
  return (
    <span
      style={{
        background: s.bg,
        color: s.color,
        padding: '2px 10px',
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      {s.text}
    </span>
  );
}

export function fmtDateTime(iso: string, tz = 'Europe/Madrid'): string {
  return new Intl.DateTimeFormat('es-ES', {
    timeZone: tz,
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(iso));
}
