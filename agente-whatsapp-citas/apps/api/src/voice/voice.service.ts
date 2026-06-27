import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '../config/config.service';
import { dateKeyInTz, weekdayInTz, parseZoned } from '../common/timezone';

@Injectable()
export class VoiceService {
  private readonly logger = new Logger('VoiceService');

  constructor(private readonly config: ConfigService) {}

  /**
   * Decides who should answer right now and builds the TwiML response.
   *
   * Decision tree:
   *   voiceEnabled=false  → forward to staff (or busy signal)
   *   voiceOverride=staff → forward to staff
   *   voiceOverride=agent → ConversationRelay
   *   voiceOverride=auto  → check voiceSchedule:
   *                           in schedule? → ConversationRelay
   *                           out of schedule? → forward to staff
   */
  async buildIncomingTwiml(callerNumber: string): Promise<string> {
    const cfg = await this.config.getRaw();

    if (!cfg.voiceEnabled) {
      return this.forwardOrBusy(cfg.staffPhone);
    }

    const override = cfg.voiceOverride ?? 'auto';

    if (override === 'staff') {
      this.logger.log('voiceOverride=staff → desviando al personal');
      return this.forwardOrBusy(cfg.staffPhone);
    }

    if (override === 'agent') {
      this.logger.log('voiceOverride=agent → agente atiende');
      return this.conversationRelayTwiml(cfg.centerName, callerNumber);
    }

    // auto — check schedule
    const tz = cfg.timezone ?? 'Europe/Madrid';
    const now = new Date();
    const weekday = weekdayInTz(now, tz);
    const todayKey = dateKeyInTz(now, tz);
    const voiceSchedule = cfg.voiceSchedule ?? [];
    const daySchedule = voiceSchedule.find((d) => d.weekday === weekday);

    let agentShouldAnswer = false;
    if (daySchedule && daySchedule.intervals.length > 0) {
      const nowMs = now.getTime();
      for (const interval of daySchedule.intervals) {
        const start = parseZoned(todayKey, interval.start, tz).getTime();
        const end = parseZoned(todayKey, interval.end, tz).getTime();
        if (nowMs >= start && nowMs < end) {
          agentShouldAnswer = true;
          break;
        }
      }
    }

    if (agentShouldAnswer) {
      this.logger.log('Horario: agente atiende');
      return this.conversationRelayTwiml(cfg.centerName, callerNumber);
    }

    this.logger.log('Fuera de horario del agente → desviando al personal');
    return this.forwardOrBusy(cfg.staffPhone);
  }

  private conversationRelayTwiml(centerName: string, callerNumber: string): string {
    const baseUrl = process.env.PUBLIC_URL ?? '';
    const wsUrl = baseUrl.replace(/^https?/, 'wss') + '/api/voice/ws';
    const greeting = `Hola, has llamado a ${centerName}. Soy el asistente virtual. ¿En qué puedo ayudarte?`;

    return `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <ConversationRelay url="${wsUrl}" welcomeGreeting="${greeting}" language="es-ES" ttsProvider="Google" voice="es-ES-Standard-A">
      <Parameter name="callerNumber" value="${callerNumber}" />
    </ConversationRelay>
  </Connect>
</Response>`;
  }

  private forwardOrBusy(staffPhone: string | null): string {
    if (staffPhone) {
      return `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial timeout="20" action="/api/voice/no-answer">
    <Number>${staffPhone}</Number>
  </Dial>
</Response>`;
    }
    // No staff phone configured — play a message and hang up.
    return `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say language="es-ES">Lo sentimos, en este momento no podemos atenderte. Por favor, llama más tarde o escríbenos por WhatsApp.</Say>
  <Hangup/>
</Response>`;
  }
}
