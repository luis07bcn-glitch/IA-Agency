import { Injectable, Logger } from '@nestjs/common';
import * as crypto from 'crypto';

/**
 * Thin client for YCloud (WhatsApp Business API).
 * Credentials come ONLY from environment variables, never from the UI.
 */
@Injectable()
export class YCloudService {
  private readonly logger = new Logger('YCloudService');

  private get apiKey(): string | undefined {
    return process.env.YCLOUD_API_KEY;
  }

  private get webhookSecret(): string | undefined {
    return process.env.YCLOUD_WEBHOOK_SECRET;
  }

  private get fromNumber(): string | undefined {
    return process.env.YCLOUD_WHATSAPP_NUMBER;
  }

  /**
   * Fail-closed signature verification. If no webhook secret is configured we
   * REJECT (never accept unsigned requests). The signature is an HMAC-SHA256
   * (hex) of the raw request body using the webhook secret. Adjust the header
   * name to match your YCloud webhook configuration if needed.
   */
  verifySignature(rawBody: Buffer | undefined, signatureHeader?: string): boolean {
    if (!this.webhookSecret) {
      this.logger.error(
        'YCLOUD_WEBHOOK_SECRET no configurado: se rechazan TODAS las peticiones (fail-closed).',
      );
      return false;
    }
    if (!rawBody || !signatureHeader) return false;

    const expected = crypto
      .createHmac('sha256', this.webhookSecret)
      .update(rawBody)
      .digest('hex');

    // Some providers prefix the signature (e.g. "sha256=..."). Normalise.
    const provided = signatureHeader.includes('=')
      ? signatureHeader.split('=').pop()!
      : signatureHeader;

    try {
      const a = Buffer.from(expected, 'hex');
      const b = Buffer.from(provided, 'hex');
      return a.length === b.length && crypto.timingSafeEqual(a, b);
    } catch {
      return false;
    }
  }

  /** Sends a plain WhatsApp text message via YCloud. */
  async sendText(to: string, body: string): Promise<void> {
    if (!this.apiKey || !this.fromNumber) {
      this.logger.warn(
        'No se envía WhatsApp: faltan YCLOUD_API_KEY o YCLOUD_WHATSAPP_NUMBER.',
      );
      return;
    }
    try {
      const res = await fetch('https://api.ycloud.com/v2/whatsapp/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey,
        },
        body: JSON.stringify({
          from: this.fromNumber,
          to,
          type: 'text',
          text: { body },
        }),
      });
      if (!res.ok) {
        // Do NOT log the message body (may contain personal data).
        this.logger.error(`YCloud respondió ${res.status} al enviar a un paciente.`);
      }
    } catch (e) {
      this.logger.error(
        `Error enviando WhatsApp: ${e instanceof Error ? e.message : e}`,
      );
    }
  }
}
