import type { Metadata } from 'next';
import './globals.css';
import { Nav } from './nav';

export const metadata: Metadata = {
  title: 'Agente de Citas',
  description: 'CRM y agente de WhatsApp para gestión de citas',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>
        <div style={{ display: 'flex', minHeight: '100vh' }}>
          <Nav />
          <main style={{ flex: 1, padding: '28px 32px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
