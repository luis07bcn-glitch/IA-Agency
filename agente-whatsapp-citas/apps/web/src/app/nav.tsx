'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const LINKS = [
  { href: '/', label: 'Inicio', icon: '📊' },
  { href: '/demo', label: 'Demo Instantánea', icon: '⚡' },
  { href: '/resultados', label: 'Resultados', icon: '📈' },
  { href: '/negocio', label: 'Tu negocio', icon: '🧠' },
  { href: '/pacientes', label: 'Pacientes', icon: '👥' },
  { href: '/calendario', label: 'Calendario', icon: '📅' },
  { href: '/conversaciones', label: 'Conversaciones', icon: '💬' },
  { href: '/whatsapp', label: 'WhatsApp', icon: '💬' },
  { href: '/voz', label: 'Voz', icon: '📞' },
  { href: '/agente', label: 'Agente', icon: '🤖' },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <aside
      style={{
        width: 230,
        background: '#0f172a',
        color: '#cbd5e1',
        padding: '24px 16px',
        flexShrink: 0,
      }}
    >
      <div style={{ fontSize: 18, fontWeight: 700, color: '#fff', padding: '0 8px 20px' }}>
        🩺 Agente de Citas
      </div>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {LINKS.map((l) => {
          const active = l.href === '/' ? pathname === '/' : pathname.startsWith(l.href);
          return (
            <Link
              key={l.href}
              href={l.href}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 12px',
                borderRadius: 8,
                textDecoration: 'none',
                color: active ? '#fff' : '#cbd5e1',
                background: active ? '#0d9488' : 'transparent',
                fontWeight: active ? 600 : 400,
              }}
            >
              <span>{l.icon}</span>
              {l.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
