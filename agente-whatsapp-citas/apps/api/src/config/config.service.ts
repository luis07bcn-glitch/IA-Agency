import { Injectable, OnModuleInit } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { AgentConfig, AGENT_CONFIG_ID } from './agent-config.entity';
import { UpdateAgentConfigDto } from './dto';
import { EventsService } from '../events/events.service';

// Shape returned to the UI: secrets replaced by has* booleans.
export interface SanitizedAgentConfig {
  centerName: string;
  description: string;
  tone: string;
  timezone: string;
  enabled: boolean;
  services: AgentConfig['services'];
  schedule: AgentConfig['schedule'];
  agentModel: string;
  hasOpenrouterApiKey: boolean;
  externalCalendarUrl: string | null;
  voiceEnabled: boolean;
  voiceOverride: 'auto' | 'agent' | 'staff';
  voiceSchedule: AgentConfig['voiceSchedule'];
  staffPhone: string | null;
  avgTicket: number | null;
  ownerPhone: string | null;
  dailyDigestEnabled: boolean;
  updatedAt: Date;
}

@Injectable()
export class ConfigService implements OnModuleInit {
  constructor(
    @InjectRepository(AgentConfig)
    private readonly repo: Repository<AgentConfig>,
    private readonly events: EventsService,
  ) {}

  async onModuleInit(): Promise<void> {
    // Ensure the single config row always exists.
    await this.getRaw();
  }

  /** Internal use only (agent, reminders). Contains the secret. */
  async getRaw(): Promise<AgentConfig> {
    let cfg = await this.repo.findOne({ where: { id: AGENT_CONFIG_ID } });
    if (!cfg) {
      cfg = this.repo.create({ id: AGENT_CONFIG_ID });
      cfg = await this.repo.save(cfg);
    }
    return cfg;
  }

  /** Safe view for the API: never includes secrets. */
  sanitize(cfg: AgentConfig): SanitizedAgentConfig {
    return {
      centerName: cfg.centerName,
      description: cfg.description,
      tone: cfg.tone,
      timezone: cfg.timezone,
      enabled: cfg.enabled,
      services: cfg.services ?? [],
      schedule: cfg.schedule ?? [],
      agentModel: cfg.agentModel,
      hasOpenrouterApiKey: !!cfg.openrouterApiKey,
      externalCalendarUrl: cfg.externalCalendarUrl ?? null,
      voiceEnabled: cfg.voiceEnabled ?? false,
      voiceOverride: cfg.voiceOverride ?? 'auto',
      voiceSchedule: cfg.voiceSchedule ?? [],
      staffPhone: cfg.staffPhone ?? null,
      avgTicket: cfg.avgTicket ?? null,
      ownerPhone: cfg.ownerPhone ?? null,
      dailyDigestEnabled: cfg.dailyDigestEnabled ?? false,
      updatedAt: cfg.updatedAt,
    };
  }

  async getSanitized(): Promise<SanitizedAgentConfig> {
    return this.sanitize(await this.getRaw());
  }

  async update(dto: UpdateAgentConfigDto): Promise<SanitizedAgentConfig> {
    const cfg = await this.getRaw();

    if (dto.centerName !== undefined) cfg.centerName = dto.centerName;
    if (dto.description !== undefined) cfg.description = dto.description;
    if (dto.tone !== undefined) cfg.tone = dto.tone;
    if (dto.timezone !== undefined) cfg.timezone = dto.timezone;
    if (dto.enabled !== undefined) cfg.enabled = dto.enabled;
    if (dto.services !== undefined) cfg.services = dto.services;
    if (dto.schedule !== undefined) cfg.schedule = dto.schedule;
    if (dto.agentModel !== undefined && dto.agentModel !== '') {
      cfg.agentModel = dto.agentModel;
    }
    if (dto.externalCalendarUrl !== undefined) {
      cfg.externalCalendarUrl = dto.externalCalendarUrl.trim() || null;
    }
    if (dto.voiceEnabled !== undefined) cfg.voiceEnabled = dto.voiceEnabled;
    if (dto.voiceOverride !== undefined && ['auto', 'agent', 'staff'].includes(dto.voiceOverride)) {
      cfg.voiceOverride = dto.voiceOverride as 'auto' | 'agent' | 'staff';
    }
    if (dto.voiceSchedule !== undefined) cfg.voiceSchedule = dto.voiceSchedule;
    if (dto.staffPhone !== undefined) cfg.staffPhone = dto.staffPhone.trim() || null;
    if (dto.avgTicket !== undefined) cfg.avgTicket = dto.avgTicket || null;
    if (dto.ownerPhone !== undefined) cfg.ownerPhone = dto.ownerPhone.trim() || null;
    if (dto.dailyDigestEnabled !== undefined) cfg.dailyDigestEnabled = dto.dailyDigestEnabled;

    // Secret handling: ignore empty/omitted so we never wipe a stored key.
    if (dto.openrouterApiKey !== undefined && dto.openrouterApiKey.trim() !== '') {
      cfg.openrouterApiKey = dto.openrouterApiKey.trim();
    }

    const saved = await this.repo.save(cfg);
    this.events.emit('agent.changed');
    return this.sanitize(saved);
  }

  /** Resolves the OpenRouter key: saved config first, env as fallback. */
  async resolveApiKey(): Promise<string | null> {
    const cfg = await this.getRaw();
    return cfg.openrouterApiKey || process.env.OPENROUTER_API_KEY || null;
  }

  /** Resolves the model id: saved config first, env as fallback. */
  async resolveModel(): Promise<string> {
    const cfg = await this.getRaw();
    return (
      cfg.agentModel ||
      process.env.AGENT_MODEL ||
      'anthropic/claude-3.5-sonnet'
    );
  }

  /** Saves extracted text from an uploaded document as the knowledge base. */
  async saveKnowledgeBase(text: string): Promise<{ characters: number }> {
    const cfg = await this.getRaw();
    cfg.knowledgeBase = text.trim();
    await this.repo.save(cfg);
    this.events.emit('agent.changed');
    return { characters: cfg.knowledgeBase.length };
  }

  /** Clears the knowledge base. */
  async clearKnowledgeBase(): Promise<void> {
    const cfg = await this.getRaw();
    cfg.knowledgeBase = null;
    await this.repo.save(cfg);
    this.events.emit('agent.changed');
  }

  /** Returns knowledge base text (for the agent system prompt). */
  async getKnowledgeBase(): Promise<string | null> {
    const cfg = await this.getRaw();
    return cfg.knowledgeBase || null;
  }
}
