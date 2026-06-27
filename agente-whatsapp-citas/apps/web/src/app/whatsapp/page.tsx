'use client';

import { useState, useEffect } from 'react';
import { api, AgentConfig } from '@/lib/api';

function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 12, padding: 20, ...style }}>
      {children}
    </div>
  );
}
function Button({ children, onClick, disabled }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean }) {
  return (
    <button onClick={onClick} disabled={disabled}
      style={{ padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--primary)', color: '#fff', fontWeight: 600, fontSize: 14, cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.6 : 1 }}>
      {children}
    </button>
  );
}

interface WaStatus {
  hasApiKey: boolean;
  hasWebhookSecret: boolean;
  phoneNumber: string | null;
  webhookUrl: string;
}

function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 14px', borderRadius: 8, background: ok ? 'rgba(72,187,120,0.1)' : 'rgba(229,62,62,0.08)', border: `1px solid ${ok ? '#48bb78' : '#e53e3e'}` }}>
      <span style={{ fontSize: 16 }}>{ok ? '✅' : '❌'}</span>
      <span style={{ fontSize: 13, fontWeight: 600, color: ok ? '#276749' : '#c53030' }}>{label}</span>
    </div>
  );
}

export default function WhatsAppPage() {
  const [cfg, setCfg] = useState<AgentConfig | null>(null);
  const [status, setStatus] = useState<WaStatus | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get<AgentConfig>('/config').then(setCfg);
    api.get<WaStatus>('/config/whatsapp-status').then(setStatus);
  }, []);

  const toggleEnabled = async () => {
    if (!cfg) return;
    setSaving(true);
    const updated = await api.put<AgentConfig>('/config', { enabled: !cfg.enabled });
    setCfg(updated);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const connected = status?.hasApiKey && status?.hasWebhookSecret;

  return (
    <div style={{ maxWidth: 780, margin: '0 auto', padding: '32px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontWeight: 800, fontSize: 26, margin: 0 }}>💬 Canal de WhatsApp</h1>
          <p style={{ color: 'var(--muted)', margin: '4px 0 0', fontSize: 14 }}>
            Configura el agente que responde los mensajes de WhatsApp del negocio.
          </p>
        </div>
        {saved && <span style={{ color: 'var(--primary)', fontWeight: 600, fontSize: 14 }}>✓ Guardado</span>}
      </div>

      {/* Estado de conexión */}
      <Card style={{ marginBottom: 20 }}>
        <h3 style={{ fontWeight: 700, marginBottom: 14 }}>Estado de la conexión</h3>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
          <StatusBadge ok={!!status?.hasApiKey} label="API key de YCloud" />
          <StatusBadge ok={!!status?.hasWebhookSecret} label="Webhook secret" />
          <StatusBadge ok={!!status?.phoneNumber} label={status?.phoneNumber ? `Número: ${status.phoneNumber}` : 'Número no configurado'} />
        </div>
        {connected
          ? <p style={{ fontSize: 13, color: '#276749', fontWeight: 600 }}>✅ WhatsApp conectado correctamente.</p>
          : <p style={{ fontSize: 13, color: 'var(--muted)' }}>Faltan datos en el archivo <code>.env</code> del servidor. Sigue las instrucciones de abajo para conectarlo.</p>
        }
      </Card>

      {/* On/Off del agente */}
      {cfg && (
        <Card style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div
              onClick={toggleEnabled}
              style={{
                width: 52, height: 28, borderRadius: 14, cursor: 'pointer', position: 'relative', flexShrink: 0,
                background: cfg.enabled ? 'var(--primary)' : 'var(--border)', transition: 'background 0.2s',
              }}
            >
              <div style={{
                position: 'absolute', top: 3, left: cfg.enabled ? 27 : 3,
                width: 22, height: 22, borderRadius: '50%', background: '#fff', transition: 'left 0.2s',
              }} />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>
                {cfg.enabled ? 'Agente activo — respondiendo mensajes' : 'Agente pausado'}
              </div>
              <div style={{ fontSize: 13, color: 'var(--muted)' }}>
                {cfg.enabled
                  ? 'El agente responde automáticamente a los mensajes de WhatsApp.'
                  : 'Los mensajes llegan pero el agente no responde. Actívalo cuando estés listo.'}
              </div>
            </div>
            {saving && <span style={{ marginLeft: 'auto', color: 'var(--muted)', fontSize: 13 }}>Guardando…</span>}
          </div>
        </Card>
      )}

      {/* Número activo */}
      {status?.phoneNumber && (
        <Card style={{ marginBottom: 20 }}>
          <h3 style={{ fontWeight: 700, marginBottom: 8 }}>Número de WhatsApp del negocio</h3>
          <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--primary)', letterSpacing: 1 }}>
            {status.phoneNumber}
          </div>
          <p style={{ fontSize: 13, color: 'var(--muted)', marginTop: 6 }}>
            Es el número al que los clientes escriben. El agente responde en su nombre.
          </p>
        </Card>
      )}

      {/* Instrucciones de conexión */}
      <Card style={{ borderLeft: '4px solid #25D366' }}>
        <h3 style={{ fontWeight: 700, marginBottom: 8 }}>Cómo conectar WhatsApp (YCloud)</h3>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
          YCloud es el servicio que enlaza el número de WhatsApp Business con nuestro sistema. Necesitas una cuenta en{' '}
          <strong>ycloud.com</strong> y un número de WhatsApp Business.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {[
            { step: '1', title: 'Crea una cuenta en YCloud', desc: 'Entra en ycloud.com y regístrate. El plan gratuito incluye suficientes mensajes para empezar.' },
            { step: '2', title: 'Registra un número de WhatsApp Business', desc: 'Puede ser un número nuevo o uno de empresa que ya tengas. YCloud te guía en el proceso de verificación con Meta.' },
            { step: '3', title: 'Copia tu API key', desc: 'En YCloud → Configuración → API. Copia la API key.' },
            { step: '4', title: 'Configura el webhook en YCloud', desc: 'En YCloud → Webhooks → añade esta URL exacta:' },
            { step: '5', title: 'Añade los datos al servidor', desc: 'Edita el archivo .env del servidor y rellena estas 3 líneas:' },
          ].map(({ step, title, desc }) => (
            <div key={step} style={{ display: 'flex', gap: 14 }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#25D366', color: '#fff', fontWeight: 800, fontSize: 13, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2 }}>
                {step}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 4 }}>{title}</div>
                <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: step === '4' || step === '5' ? 8 : 0 }}>{desc}</div>
                {step === '4' && status && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <code style={{ background: 'var(--bg)', padding: '6px 12px', borderRadius: 6, fontSize: 12, flex: 1, wordBreak: 'break-all' }}>
                      {status.webhookUrl}
                    </code>
                    <button
                      onClick={() => navigator.clipboard.writeText(status.webhookUrl)}
                      style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border)', background: 'transparent', cursor: 'pointer', fontSize: 12, fontWeight: 600 }}
                    >
                      Copiar
                    </button>
                  </div>
                )}
                {step === '5' && (
                  <pre style={{ background: 'var(--bg)', borderRadius: 8, padding: 14, fontSize: 12, margin: 0 }}>
{`YCLOUD_API_KEY=tu-api-key-de-ycloud
YCLOUD_WEBHOOK_SECRET=secreto-que-defines-tu
YCLOUD_WHATSAPP_NUMBER=+34600000000`}
                  </pre>
                )}
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 20, padding: 14, borderRadius: 8, background: 'rgba(37,211,102,0.08)', border: '1px solid rgba(37,211,102,0.3)' }}>
          <p style={{ fontSize: 13, margin: 0, color: 'var(--text)' }}>
            <strong>Nota:</strong> Los secretos (API key y webhook secret) se guardan en el servidor, nunca en este panel. Una vez configurados, el estado de arriba se pondrá en verde automáticamente.
          </p>
        </div>
      </Card>
    </div>
  );
}
