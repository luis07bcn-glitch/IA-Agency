import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Between, Repository } from 'typeorm';
import { Appointment } from '../appointments/appointment.entity';
import { Conversation } from '../conversations/conversation.entity';
import { Message } from '../conversations/message.entity';
import { ConfigService } from '../config/config.service';

export interface RoiMetrics {
  periodDays: number;
  // Core counters
  appointmentsByAgent: number;
  appointmentsTotal: number;
  completed: number;
  noShow: number;
  cancelled: number;
  messagesHandled: number;
  whatsappConversations: number;
  // Derived
  estimatedRevenue: number | null; // null if no avgTicket configured
  avgTicket: number | null;
  noShowRate: number; // 0..1
  // Comparison vs previous period (% change, can be negative)
  deltaAppointmentsByAgent: number | null;
  deltaMessages: number | null;
}

@Injectable()
export class MetricsService {
  constructor(
    @InjectRepository(Appointment)
    private readonly appts: Repository<Appointment>,
    @InjectRepository(Conversation)
    private readonly conversations: Repository<Conversation>,
    @InjectRepository(Message)
    private readonly messages: Repository<Message>,
    private readonly config: ConfigService,
  ) {}

  /** ROI metrics for the last `periodDays` days (default 30). */
  async roi(periodDays = 30): Promise<RoiMetrics> {
    const cfg = await this.config.getRaw();
    const now = new Date();
    const start = new Date(now.getTime() - periodDays * 24 * 3600 * 1000);
    const prevStart = new Date(start.getTime() - periodDays * 24 * 3600 * 1000);

    const [
      appointmentsByAgent,
      appointmentsTotal,
      completed,
      noShow,
      cancelled,
      messagesHandled,
      whatsappConversations,
      prevAppointmentsByAgent,
      prevMessages,
    ] = await Promise.all([
      this.countAppointments({ start, end: now, source: 'agent', by: 'created' }),
      this.countAppointments({ start, end: now, by: 'created' }),
      this.countAppointments({ start, end: now, status: 'completed', by: 'starts' }),
      this.countAppointments({ start, end: now, status: 'no_show', by: 'starts' }),
      this.countAppointments({ start, end: now, status: 'cancelled', by: 'starts' }),
      this.countAgentMessages(start, now),
      this.countWhatsappConversations(start, now),
      this.countAppointments({ start: prevStart, end: start, source: 'agent', by: 'created' }),
      this.countAgentMessages(prevStart, start),
    ]);

    const avgTicket = cfg.avgTicket ?? null;
    const estimatedRevenue = avgTicket != null ? appointmentsByAgent * avgTicket : null;
    const noShowRate = completed + noShow > 0 ? noShow / (completed + noShow) : 0;

    return {
      periodDays,
      appointmentsByAgent,
      appointmentsTotal,
      completed,
      noShow,
      cancelled,
      messagesHandled,
      whatsappConversations,
      estimatedRevenue,
      avgTicket,
      noShowRate,
      deltaAppointmentsByAgent: pctChange(prevAppointmentsByAgent, appointmentsByAgent),
      deltaMessages: pctChange(prevMessages, messagesHandled),
    };
  }

  private countAppointments(opts: {
    start: Date;
    end: Date;
    source?: 'agent' | 'manual';
    status?: string;
    by: 'created' | 'starts';
  }): Promise<number> {
    const where: Record<string, unknown> = {
      [opts.by === 'created' ? 'createdAt' : 'startsAt']: Between(opts.start, opts.end),
    };
    if (opts.source) where.source = opts.source;
    if (opts.status) where.status = opts.status;
    return this.appts.count({ where });
  }

  /** Messages sent BY the agent on WhatsApp threads in the window. */
  private async countAgentMessages(start: Date, end: Date): Promise<number> {
    return this.messages
      .createQueryBuilder('m')
      .innerJoin('m.conversation', 'c')
      .where('m.role = :role', { role: 'assistant' })
      .andWhere('c.channel = :channel', { channel: 'whatsapp' })
      .andWhere('m.createdAt BETWEEN :start AND :end', { start, end })
      .getCount();
  }

  /** Distinct WhatsApp conversations active in the window. */
  private async countWhatsappConversations(start: Date, end: Date): Promise<number> {
    return this.conversations.count({
      where: { channel: 'whatsapp', lastMessageAt: Between(start, end) },
    });
  }
}

/** % change from a to b. null if no baseline. */
function pctChange(a: number, b: number): number | null {
  if (a === 0) return b > 0 ? 100 : null;
  return Math.round(((b - a) / a) * 100);
}
