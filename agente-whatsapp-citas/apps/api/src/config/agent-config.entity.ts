import { Column, Entity, PrimaryColumn, UpdateDateColumn } from 'typeorm';

export interface Service {
  name: string;
  durationMin: number;
}

// Opening hours per weekday. Each day has a list of intervals "HH:mm"-"HH:mm".
export interface DaySchedule {
  // 0 = Sunday ... 6 = Saturday (JS getDay convention).
  weekday: number;
  intervals: { start: string; end: string }[];
}

// Single-tenant: there is exactly ONE row, with a fixed id.
export const AGENT_CONFIG_ID = 1;

@Entity('agent_config')
export class AgentConfig {
  @PrimaryColumn({ type: 'int' })
  id: number;

  // --- Center persona ---
  @Column({ default: 'Mi Centro' })
  centerName: string;

  @Column({ type: 'text', default: '' })
  description: string;

  @Column({ default: 'cercano y profesional' })
  tone: string;

  @Column({ default: 'Europe/Madrid' })
  timezone: string;

  // WhatsApp channel on/off (this is what currently gates the WhatsApp agent).
  @Column({ default: true })
  enabled: boolean;

  // --- Voice channel (independent of WhatsApp; can be sold separately) ---
  // Whether the voice channel is active at all for this client.
  @Column({ default: false })
  voiceEnabled: boolean;

  // Instant manual switch (Mando B):
  //  'auto'  -> follow voiceSchedule (agent answers in those hours, else staff)
  //  'agent' -> force the agent to answer all calls now
  //  'staff' -> force forward to staff now ("ahora contesto yo")
  @Column({ default: 'auto' })
  voiceOverride: 'auto' | 'agent' | 'staff';

  // Hours the agent answers calls automatically (Mando A). Same shape as schedule.
  @Column({ type: 'jsonb', default: () => "'[]'" })
  voiceSchedule: DaySchedule[];

  // Phone number to forward calls to when the agent is NOT answering (E.164).
  @Column({ type: 'varchar', nullable: true })
  staffPhone: string | null;

  // --- Services & schedule ---
  @Column({ type: 'jsonb', default: () => "'[]'" })
  services: Service[];

  @Column({ type: 'jsonb', default: () => "'[]'" })
  schedule: DaySchedule[];

  // --- AI model (OpenRouter) ---
  // SECRET: never returned by the API (sanitized to a has* boolean).
  @Column({ type: 'varchar', nullable: true })
  openrouterApiKey: string | null;

  @Column({ default: 'anthropic/claude-3.5-sonnet' })
  agentModel: string;

  // Knowledge base: plain text extracted from uploaded PDFs/docs.
  @Column({ type: 'text', nullable: true })
  knowledgeBase: string | null;

  // External calendar iCal URL (Google Calendar, TheFork, CoverManager, Outlook…)
  // Used to avoid double-booking with existing reservation systems.
  @Column({ type: 'text', nullable: true })
  externalCalendarUrl: string | null;

  // --- ROI / business metrics ---
  // Average ticket value (€) per appointment — used to estimate revenue generated.
  @Column({ type: 'int', nullable: true })
  avgTicket: number | null;

  // Owner phone (E.164) to receive the daily WhatsApp digest.
  @Column({ type: 'varchar', nullable: true })
  ownerPhone: string | null;

  // Whether to send the owner a daily summary over WhatsApp.
  @Column({ default: false })
  dailyDigestEnabled: boolean;

  @UpdateDateColumn({ type: 'timestamptz' })
  updatedAt: Date;
}
