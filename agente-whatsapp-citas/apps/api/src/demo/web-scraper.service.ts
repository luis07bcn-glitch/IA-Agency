import { Injectable, Logger } from '@nestjs/common';

const MAX_BYTES = 600_000; // cap download size
const MAX_TEXT = 12_000; // cap text handed to the LLM
const TIMEOUT_MS = 12_000;

/**
 * Fetches a business homepage and reduces it to plain text for the LLM.
 *
 * SSRF guard: only public http(s) hosts are allowed. Private / loopback /
 * link-local ranges and non-http schemes are rejected, since the demo builder
 * fetches URLs that originate from external data (Google Places / user input).
 */
@Injectable()
export class WebScraperService {
  private readonly logger = new Logger('WebScraperService');

  /** Returns extracted homepage text, or null if the site can't be read safely. */
  async fetchText(rawUrl: string | null | undefined): Promise<string | null> {
    if (!rawUrl) return null;

    let url: URL;
    try {
      url = new URL(rawUrl);
    } catch {
      return null;
    }

    if (url.protocol !== 'http:' && url.protocol !== 'https:') return null;
    if (this.isBlockedHost(url.hostname)) {
      this.logger.warn(`Bloqueado host no público: ${url.hostname}`);
      return null;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    try {
      const res = await fetch(url.toString(), {
        signal: controller.signal,
        redirect: 'follow',
        headers: { 'User-Agent': 'MerakIA-DemoBot/1.0 (+agente de citas)' },
      });
      if (!res.ok) return null;

      const type = res.headers.get('content-type') ?? '';
      if (!type.includes('text/html') && !type.includes('text/plain')) return null;

      const buf = await this.readCapped(res);
      const text = this.htmlToText(buf);
      return text.slice(0, MAX_TEXT) || null;
    } catch (e) {
      this.logger.warn(`No se pudo leer la web: ${e instanceof Error ? e.message : e}`);
      return null;
    } finally {
      clearTimeout(timer);
    }
  }

  /** Reads the response body but stops once MAX_BYTES is exceeded. */
  private async readCapped(res: Response): Promise<string> {
    const reader = res.body?.getReader();
    if (!reader) return await res.text();

    const decoder = new TextDecoder();
    let out = '';
    let total = 0;
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      total += value.byteLength;
      out += decoder.decode(value, { stream: true });
      if (total >= MAX_BYTES) {
        await reader.cancel().catch(() => undefined);
        break;
      }
    }
    return out;
  }

  /** Crude but dependency-free HTML → text. */
  private htmlToText(html: string): string {
    return html
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style[\s\S]*?<\/style>/gi, ' ')
      .replace(/<noscript[\s\S]*?<\/noscript>/gi, ' ')
      .replace(/<[^>]+>/g, ' ')
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&[a-z]+;/gi, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  /** Blocks loopback, private, link-local and obviously-internal hostnames. */
  private isBlockedHost(host: string): boolean {
    const h = host.toLowerCase();
    if (h === 'localhost' || h.endsWith('.localhost') || h.endsWith('.local')) return true;
    if (h === '0.0.0.0' || h === '::1' || h === '[::1]') return true;

    // IPv4 private / loopback / link-local / CGNAT ranges.
    const m = h.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
    if (m) {
      const [a, b] = [Number(m[1]), Number(m[2])];
      if (a === 10 || a === 127) return true;
      if (a === 192 && b === 168) return true;
      if (a === 172 && b >= 16 && b <= 31) return true;
      if (a === 169 && b === 254) return true; // link-local
      if (a === 100 && b >= 64 && b <= 127) return true; // CGNAT
    }
    return false;
  }
}
