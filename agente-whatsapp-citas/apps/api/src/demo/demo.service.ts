import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '../config/config.service';
import { PlacesService, PlaceDetails } from './places.service';
import { WebScraperService } from './web-scraper.service';

export interface DemoConfig {
  centerName: string;
  description: string;
  tone: string;
  timezone: string;
  services: { name: string; durationMin: number }[];
  schedule: { weekday: number; intervals: { start: string; end: string }[] }[];
}

export interface GeneratedDemo {
  found: boolean;
  source: {
    name: string;
    address: string | null;
    phone: string | null;
    website: string | null;
    googleMapsUri: string | null;
    primaryType: string | null;
    rating: number | null;
    userRatingCount: number;
  };
  config: DemoConfig;
  knowledgeBase: string;
  welcomeMessage: string;
  highlights: string[];
}

@Injectable()
export class DemoService {
  private readonly logger = new Logger('DemoService');

  constructor(
    private readonly config: ConfigService,
    private readonly places: PlacesService,
    private readonly scraper: WebScraperService,
  ) {}

  get isConfigured(): boolean {
    return this.places.isConfigured;
  }

  /** Looks up a business by name + city and builds a ready-to-talk-to agent. */
  async build(name: string, city: string): Promise<GeneratedDemo> {
    const query = [name, city].filter(Boolean).join(' ').trim();
    if (!query) throw new Error('Indica al menos el nombre del negocio.');

    const match = await this.places.findTopMatch(query);
    if (!match) {
      return this.empty(name);
    }

    const details = await this.places.getDetails(match.placeId);
    const webText = await this.scraper.fetchText(details.website);
    const generated = await this.extractConfig(details, webText);

    return {
      found: true,
      source: {
        name: details.name,
        address: details.address,
        phone: details.phone,
        website: details.website,
        googleMapsUri: details.googleMapsUri,
        primaryType: details.primaryType,
        rating: details.rating,
        userRatingCount: details.userRatingCount,
      },
      ...generated,
    };
  }

  /** Conversational reply for the demo chat. No real tools / no DB writes. */
  async chat(
    config: DemoConfig,
    knowledgeBase: string,
    history: { role: 'user' | 'assistant'; content: string }[],
    message: string,
  ): Promise<string> {
    const system = this.buildDemoSystemPrompt(config, knowledgeBase);
    // Anthropic requires the first message to be from the user; drop the leading
    // assistant welcome (and any stray leading assistant turns) before sending.
    const cleaned = [...history];
    while (cleaned.length && cleaned[0].role === 'assistant') cleaned.shift();
    const messages = [...cleaned, { role: 'user' as const, content: message }];
    return this.callLLM(system, messages, 600);
  }

  /** Persists the (possibly edited) generated config as the live agent config. */
  async apply(config: DemoConfig, knowledgeBase: string): Promise<{ ok: true }> {
    await this.config.update({
      centerName: config.centerName,
      description: config.description,
      tone: config.tone,
      timezone: this.safeTimezone(config.timezone),
      services: config.services,
      schedule: config.schedule,
    });
    if (knowledgeBase?.trim()) {
      await this.config.saveKnowledgeBase(knowledgeBase.trim());
    }
    return { ok: true };
  }

  // ---- internals ----

  private empty(name: string): GeneratedDemo {
    return {
      found: false,
      source: {
        name,
        address: null,
        phone: null,
        website: null,
        googleMapsUri: null,
        primaryType: null,
        rating: null,
        userRatingCount: 0,
      },
      config: {
        centerName: name,
        description: '',
        tone: 'cercano y profesional',
        timezone: 'Europe/Madrid',
        services: [],
        schedule: [],
      },
      knowledgeBase: '',
      welcomeMessage: '',
      highlights: [],
    };
  }

  private async extractConfig(
    d: PlaceDetails,
    webText: string | null,
  ): Promise<Omit<GeneratedDemo, 'found' | 'source'>> {
    const reviewsBlock = d.reviews
      .slice(0, 6)
      .map((r) => `(${r.rating}★) ${r.text}`)
      .join('\n');

    const input = [
      `NOMBRE: ${d.name}`,
      d.primaryType ? `TIPO: ${d.primaryType}` : '',
      d.address ? `DIRECCIÓN: ${d.address}` : '',
      d.phone ? `TELÉFONO: ${d.phone}` : '',
      d.rating ? `VALORACIÓN GOOGLE: ${d.rating} (${d.userRatingCount} reseñas)` : '',
      d.editorialSummary ? `DESCRIPCIÓN GOOGLE: ${d.editorialSummary}` : '',
      d.openingHours.length ? `HORARIOS GOOGLE:\n${d.openingHours.join('\n')}` : '',
      reviewsBlock ? `RESEÑAS:\n${reviewsBlock}` : '',
      webText ? `TEXTO DE SU WEB:\n${webText}` : '',
    ]
      .filter(Boolean)
      .join('\n\n');

    const system = `Eres un experto en configurar asistentes de reservas/citas para negocios locales (restaurantes, clínicas, peluquerías, etc.).
Te doy datos reales de un negocio (Google + su web). Devuelve SOLO un objeto JSON válido, sin texto alrededor, con esta forma exacta:

{
  "description": "1-2 frases describiendo el negocio para el asistente",
  "tone": "tono de voz recomendado (p.ej. 'cercano y profesional')",
  "timezone": "IANA timezone (España -> Europe/Madrid)",
  "services": [{"name": "Servicio reservable", "durationMin": 60}],
  "schedule": [{"weekday": 1, "intervals": [{"start":"09:00","end":"14:00"}]}],
  "knowledgeBase": "Ficha de información útil para responder: especialidades, precios si los hay, ubicación, parking, idiomas, políticas. Texto plano.",
  "welcomeMessage": "Primer mensaje de bienvenida del asistente por WhatsApp, en su nombre",
  "highlights": ["3-5 bullets MUY cortos de lo que el asistente ha aprendido del negocio"]
}

REGLAS:
- weekday: 0=domingo, 1=lunes, ... 6=sábado. Usa los HORARIOS GOOGLE si están; si no, infiere un horario típico del sector.
- "services" deben ser cosas reservables reales del sector (restaurante: "Reserva mesa comida", "Reserva mesa cena", "Evento privado"; clínica: tratamientos concretos; peluquería: cortes, color...).
- Sé concreto y usa los datos reales. NO inventes precios que no aparezcan. Español. Devuelve SOLO el JSON.`;

    let parsed: any = {};
    try {
      const raw = await this.callLLM(system, [{ role: 'user', content: input }], 2000);
      parsed = this.parseJson(raw);
    } catch (e) {
      this.logger.warn(`Fallo extrayendo config: ${e instanceof Error ? e.message : e}`);
    }

    const config: DemoConfig = {
      centerName: d.name,
      description: typeof parsed.description === 'string' ? parsed.description : (d.editorialSummary ?? ''),
      tone: typeof parsed.tone === 'string' ? parsed.tone : 'cercano y profesional',
      timezone: this.safeTimezone(parsed.timezone),
      services: this.normalizeServices(parsed.services),
      schedule: this.normalizeSchedule(parsed.schedule),
    };

    return {
      config,
      knowledgeBase: typeof parsed.knowledgeBase === 'string' ? parsed.knowledgeBase : '',
      welcomeMessage:
        typeof parsed.welcomeMessage === 'string'
          ? parsed.welcomeMessage
          : `¡Hola! Soy el asistente de ${d.name}. ¿En qué puedo ayudarte?`,
      highlights: Array.isArray(parsed.highlights)
        ? parsed.highlights.filter((h: unknown) => typeof h === 'string').slice(0, 6)
        : [],
    };
  }

  private buildDemoSystemPrompt(cfg: DemoConfig, knowledgeBase: string): string {
    const services = (cfg.services ?? []).map((s) => `- ${s.name} (${s.durationMin} min)`).join('\n');
    const dayNames = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
    const schedule = (cfg.schedule ?? [])
      .map(
        (d) =>
          `- ${dayNames[d.weekday]}: ${
            d.intervals.length ? d.intervals.map((i) => `${i.start}-${i.end}`).join(', ') : 'cerrado'
          }`,
      )
      .join('\n');

    return `Eres el asistente de reservas de "${cfg.centerName}".
${cfg.description ? cfg.description + '\n' : ''}
Tono: ${cfg.tone}. Hablas en español, breve y natural (es WhatsApp).
Zona horaria: ${cfg.timezone}.

SERVICIOS:
${services || '- (genéricos del sector)'}

HORARIOS:
${schedule || '- (horario habitual del sector)'}

ESTO ES UNA DEMOSTRACIÓN para enseñar al dueño cómo atendería su asistente.
- Atiende como su recepcionista: responde dudas, propón horas y "confirma" reservas de forma natural.
- No hay agenda real conectada: actúa como si pudieras reservar, sin prometer nada técnico.
- Mensajes cortos y cálidos, una sola pregunta o acción por mensaje. Sin markdown.
${
  knowledgeBase
    ? `\nINFORMACIÓN DEL NEGOCIO (úsala para precios, especialidades, ubicación, políticas):\n${knowledgeBase}`
    : ''
}`;
  }

  /** Single entry point for LLM calls — branches on the configured key. */
  private async callLLM(
    system: string,
    messages: { role: 'user' | 'assistant'; content: string }[],
    maxTokens: number,
  ): Promise<string> {
    const apiKey = await this.config.resolveApiKey();
    if (!apiKey) throw new Error('No hay API key del modelo configurada.');
    const model = await this.config.resolveModel();

    if (apiKey.startsWith('sk-ant-')) {
      const res = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json',
        },
        body: JSON.stringify({ model, max_tokens: maxTokens, system, messages }),
      });
      if (!res.ok) throw new Error(`Anthropic ${res.status}: ${await res.text()}`);
      const data = (await res.json()) as { content: { type: string; text?: string }[] };
      return (data.content.find((b) => b.type === 'text')?.text ?? '').trim();
    }

    // OpenRouter (OpenAI-compatible).
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        max_tokens: maxTokens,
        messages: [{ role: 'system', content: system }, ...messages],
      }),
    });
    if (!res.ok) throw new Error(`OpenRouter ${res.status}: ${await res.text()}`);
    const data = (await res.json()) as any;
    return (data.choices?.[0]?.message?.content ?? '').trim();
  }

  private parseJson(raw: string): any {
    let s = raw.trim();
    // strip code fences if present
    const fence = s.match(/```(?:json)?\s*([\s\S]*?)```/i);
    if (fence) s = fence[1].trim();
    const start = s.indexOf('{');
    const end = s.lastIndexOf('}');
    if (start === -1 || end === -1) throw new Error('Respuesta sin JSON.');
    return JSON.parse(s.slice(start, end + 1));
  }

  private normalizeServices(raw: unknown): DemoConfig['services'] {
    if (!Array.isArray(raw)) return [];
    return raw
      .map((s: any) => ({
        name: String(s?.name ?? '').trim(),
        durationMin: Number.isFinite(Number(s?.durationMin)) ? Math.max(5, Math.round(Number(s.durationMin))) : 60,
      }))
      .filter((s) => s.name.length > 0)
      .slice(0, 12);
  }

  private normalizeSchedule(raw: unknown): DemoConfig['schedule'] {
    if (!Array.isArray(raw)) return [];
    const out: DemoConfig['schedule'] = [];
    for (const d of raw as any[]) {
      const weekday = Number(d?.weekday);
      if (!Number.isInteger(weekday) || weekday < 0 || weekday > 6) continue;
      const intervals = Array.isArray(d?.intervals)
        ? d.intervals
            .map((i: any) => ({ start: String(i?.start ?? ''), end: String(i?.end ?? '') }))
            .filter((i: { start: string; end: string }) => /^\d{1,2}:\d{2}$/.test(i.start) && /^\d{1,2}:\d{2}$/.test(i.end))
        : [];
      out.push({ weekday, intervals });
    }
    return out;
  }

  private safeTimezone(tz: unknown): string {
    const value = typeof tz === 'string' && tz.trim() ? tz.trim() : 'Europe/Madrid';
    try {
      new Intl.DateTimeFormat('es-ES', { timeZone: value });
      return value;
    } catch {
      return 'Europe/Madrid';
    }
  }
}
