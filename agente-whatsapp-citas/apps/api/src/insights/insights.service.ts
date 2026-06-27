import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { In, MoreThanOrEqual, Repository } from 'typeorm';
import { Conversation } from '../conversations/conversation.entity';
import { Message } from '../conversations/message.entity';
import { Appointment } from '../appointments/appointment.entity';
import { ConfigService } from '../config/config.service';
import { callLLM, parseLlmJson } from '../common/llm';

const MAX_CONVERSATIONS = 120;
const MAX_MSGS_PER_CONVO = 24;
const MAX_CORPUS_CHARS = 48_000;

export interface InsightAnswer {
  answer: string;
  basedOn: { conversations: number; messages: number; periodDays: number };
}

export interface ReportFinding {
  emoji: string;
  category: string;
  title: string;
  detail: string;
  quote: string | null;
  action: string;
}

export interface BusinessReport {
  summary: string;
  findings: ReportFinding[];
  basedOn: { conversations: number; messages: number; periodDays: number };
}

/**
 * "Habla con tu negocio": turns the stream of real customer conversations into
 * answerable business intelligence. Read-only — never writes to the DB.
 */
@Injectable()
export class InsightsService {
  private readonly logger = new Logger('InsightsService');

  constructor(
    @InjectRepository(Conversation) private readonly convos: Repository<Conversation>,
    @InjectRepository(Message) private readonly messages: Repository<Message>,
    @InjectRepository(Appointment) private readonly appointments: Repository<Appointment>,
    private readonly config: ConfigService,
  ) {}

  suggestions(): string[] {
    return [
      '¿Qué me piden mis clientes que no ofrezco?',
      '¿Por qué cancela o no aparece la gente?',
      '¿Qué es lo que más frustra a mis clientes?',
      '¿Qué horas o días me están pidiendo y no tengo hueco?',
      '¿Mencionan a la competencia? ¿Qué dicen?',
      '¿Qué debería añadir a mis servicios o a mi carta?',
    ];
  }

  /** Free-form question answered strictly from the conversation + booking data. */
  async ask(question: string, days = 30): Promise<InsightAnswer> {
    const corpus = await this.buildCorpus(days);
    const stats = await this.buildStats(days);
    const cfg = await this.config.getRaw();

    const apiKey = await this.config.resolveApiKey();
    if (!apiKey) throw new Error('No hay API key del modelo configurada.');
    const model = await this.config.resolveModel();

    if (corpus.conversationCount === 0) {
      return {
        answer:
          'Todavía no hay conversaciones de clientes en este periodo, así que no puedo sacar conclusiones. En cuanto el asistente empiece a atender por WhatsApp, aquí tendrás respuestas basadas en lo que realmente dice tu gente.',
        basedOn: { conversations: 0, messages: 0, periodDays: days },
      };
    }

    const system = `Eres un consultor de negocio analizando las conversaciones REALES entre el negocio "${cfg.centerName}" y sus clientes (por WhatsApp).
Respondes la pregunta del dueño basándote ÚNICAMENTE en los datos que te doy (conversaciones + estadísticas de citas).
REGLAS:
- Sé concreto y accionable. Da números aproximados cuando puedas ("unas 12 personas...").
- Cuando afirmes algo, apóyalo con 1-2 CITAS textuales de clientes entre comillas.
- Si los datos no bastan para responder, dilo claramente; no inventes.
- Español, tono directo de asesor. Sin markdown pesado; frases claras. Máximo ~200 palabras.`;

    const user = `PREGUNTA DEL DUEÑO:\n${question}\n\n=== ESTADÍSTICAS DE CITAS (${days} días) ===\n${stats}\n\n=== CONVERSACIONES CON CLIENTES ===\n${corpus.text}`;

    try {
      const answer = await callLLM({
        apiKey,
        model,
        system,
        messages: [{ role: 'user', content: user }],
        maxTokens: 700,
      });
      return {
        answer: answer || 'No he podido generar una respuesta. Inténtalo de nuevo.',
        basedOn: {
          conversations: corpus.conversationCount,
          messages: corpus.messageCount,
          periodDays: days,
        },
      };
    } catch (e) {
      this.logger.error(`Error en ask: ${e instanceof Error ? e.message : e}`);
      throw new Error('No se pudo analizar ahora mismo. Revisa la API key del modelo.');
    }
  }

  /** Structured weekly-style report of what customers have been saying. */
  async report(days = 30): Promise<BusinessReport> {
    const corpus = await this.buildCorpus(days);
    const stats = await this.buildStats(days);
    const cfg = await this.config.getRaw();
    const basedOn = {
      conversations: corpus.conversationCount,
      messages: corpus.messageCount,
      periodDays: days,
    };

    if (corpus.conversationCount === 0) {
      return {
        summary: 'Aún no hay suficientes conversaciones para un informe.',
        findings: [],
        basedOn,
      };
    }

    const apiKey = await this.config.resolveApiKey();
    if (!apiKey) throw new Error('No hay API key del modelo configurada.');
    const model = await this.config.resolveModel();

    const system = `Eres un consultor de negocio. Analizas conversaciones REALES entre "${cfg.centerName}" y sus clientes y devuelves un informe ejecutivo.
Devuelve SOLO un objeto JSON válido con esta forma exacta:
{
  "summary": "1 frase con el titular más importante de la semana",
  "findings": [
    {
      "emoji": "un emoji",
      "category": "Demanda no cubierta | Queja/fricción | Competencia | Pregunta sin resolver | Oportunidad de ingreso",
      "title": "titular corto del hallazgo",
      "detail": "1-2 frases con número aproximado de veces que aparece",
      "quote": "cita textual de un cliente, o null",
      "action": "recomendación corta y accionable"
    }
  ]
}
REGLAS: 3-6 hallazgos, los MÁS relevantes y accionables. Solo lo que se deduzca de los datos (no inventes). Español. SOLO el JSON.`;

    const user = `=== ESTADÍSTICAS DE CITAS (${days} días) ===\n${stats}\n\n=== CONVERSACIONES CON CLIENTES ===\n${corpus.text}`;

    try {
      const raw = await callLLM({
        apiKey,
        model,
        system,
        messages: [{ role: 'user', content: user }],
        maxTokens: 1800,
      });
      const parsed = parseLlmJson<{ summary?: string; findings?: any[] }>(raw);
      return {
        summary: typeof parsed.summary === 'string' ? parsed.summary : 'Informe de tus clientes',
        findings: this.normalizeFindings(parsed.findings),
        basedOn,
      };
    } catch (e) {
      this.logger.error(`Error en report: ${e instanceof Error ? e.message : e}`);
      throw new Error('No se pudo generar el informe ahora mismo.');
    }
  }

  // ---- internals ----

  private normalizeFindings(raw: unknown): ReportFinding[] {
    if (!Array.isArray(raw)) return [];
    return raw
      .map((f: any) => ({
        emoji: typeof f?.emoji === 'string' ? f.emoji : '📌',
        category: String(f?.category ?? '').trim() || 'Hallazgo',
        title: String(f?.title ?? '').trim(),
        detail: String(f?.detail ?? '').trim(),
        quote: typeof f?.quote === 'string' && f.quote.trim() ? f.quote.trim() : null,
        action: String(f?.action ?? '').trim(),
      }))
      .filter((f) => f.title.length > 0)
      .slice(0, 6);
  }

  private async buildCorpus(
    days: number,
  ): Promise<{ text: string; conversationCount: number; messageCount: number }> {
    const cutoff = new Date(Date.now() - days * 86_400_000);
    const convos = await this.convos.find({
      where: { lastMessageAt: MoreThanOrEqual(cutoff) },
      order: { lastMessageAt: 'DESC' },
      take: MAX_CONVERSATIONS,
    });
    if (convos.length === 0) return { text: '', conversationCount: 0, messageCount: 0 };

    const ids = convos.map((c) => c.id);
    const msgs = await this.messages.find({
      where: { conversationId: In(ids) },
      order: { createdAt: 'ASC' },
    });

    const byConvo = new Map<string, Message[]>();
    for (const m of msgs) {
      if (m.role === 'system') continue;
      const list = byConvo.get(m.conversationId) ?? [];
      list.push(m);
      byConvo.set(m.conversationId, list);
    }

    const blocks: string[] = [];
    let total = 0;
    let usedConvos = 0;
    let usedMsgs = 0;
    for (const c of convos) {
      const list = (byConvo.get(c.id) ?? []).slice(-MAX_MSGS_PER_CONVO);
      if (list.length === 0) continue;
      const date = c.lastMessageAt.toISOString().slice(0, 10);
      const lines = list.map((m) => {
        usedMsgs++;
        const who = m.role === 'user' ? 'Cliente' : 'Asistente';
        return `${who}: ${m.text.replace(/\s+/g, ' ').trim()}`;
      });
      const block = `--- Conversación (${date}) ---\n${lines.join('\n')}`;
      if (total + block.length > MAX_CORPUS_CHARS) break;
      blocks.push(block);
      total += block.length;
      usedConvos++;
    }

    return { text: blocks.join('\n\n'), conversationCount: usedConvos, messageCount: usedMsgs };
  }

  private async buildStats(days: number): Promise<string> {
    const cutoff = new Date(Date.now() - days * 86_400_000);
    const now = new Date();
    const appts = await this.appointments.find({
      where: { startsAt: MoreThanOrEqual(cutoff) },
    });

    const past = appts.filter((a) => a.startsAt <= now);
    const byStatus = { completed: 0, cancelled: 0, no_show: 0, scheduled: 0 };
    const byService = new Map<string, number>();
    for (const a of appts) {
      byStatus[a.status] = (byStatus[a.status] ?? 0) + 1;
      byService.set(a.serviceName, (byService.get(a.serviceName) ?? 0) + 1);
    }
    const topServices = [...byService.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([name, n]) => `${name}: ${n}`)
      .join('; ');

    return [
      `Citas creadas: ${appts.length} (${past.length} ya pasadas).`,
      `Completadas: ${byStatus.completed}. Canceladas: ${byStatus.cancelled}. No-shows (ausencias): ${byStatus.no_show}. Próximas: ${byStatus.scheduled}.`,
      topServices ? `Servicios más reservados: ${topServices}.` : 'Sin servicios reservados aún.',
    ].join('\n');
  }
}
