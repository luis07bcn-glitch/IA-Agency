import { Injectable, Logger } from '@nestjs/common';
import { YCloudService } from './ycloud.service';
import { PatientsService } from '../patients/patients.service';
import { ConversationsService } from '../conversations/conversations.service';
import { AgentService } from '../agent/agent.service';

// Defensive parser for YCloud inbound message payloads.
interface ParsedInbound {
  phone: string;
  text: string;
  name?: string;
}

function parseInbound(payload: any): ParsedInbound | null {
  // YCloud wraps the WhatsApp inbound message; shapes vary by event type.
  const msg =
    payload?.whatsappInboundMessage ??
    payload?.data?.whatsappInboundMessage ??
    payload;

  const phone = msg?.from ?? msg?.customerProfile?.phoneNumber;
  const text =
    msg?.text?.body ?? msg?.text ?? msg?.body ?? msg?.message?.text?.body;
  const name = msg?.customerProfile?.name;

  if (!phone || !text || typeof text !== 'string') return null;
  return { phone: String(phone), text, name };
}

@Injectable()
export class WebhooksService {
  private readonly logger = new Logger('WebhooksService');

  constructor(
    private readonly ycloud: YCloudService,
    private readonly patients: PatientsService,
    private readonly conversations: ConversationsService,
    private readonly agent: AgentService,
  ) {}

  /**
   * Processes an inbound WhatsApp message end to end. Called AFTER the webhook
   * has already returned 200, so it runs in the background.
   */
  async handleInbound(payload: any): Promise<void> {
    const parsed = parseInbound(payload);
    if (!parsed) {
      this.logger.debug('Webhook recibido sin mensaje de texto procesable.');
      return;
    }

    try {
      // 1. Upsert the patient by phone.
      const patient = await this.patients.upsertByPhone(
        parsed.phone,
        parsed.name,
      );

      // 2. Get/create the WhatsApp thread and store the inbound message.
      const thread = await this.conversations.getOrCreateWhatsappThread(
        patient.phone,
        patient.id,
        patient.name,
      );
      await this.conversations.addMessage(thread.id, 'user', parsed.text);

      // 3. The agent responds.
      const history = await this.conversations.historyForAgent(thread.id);
      const reply = await this.agent.generateReply({
        conversationId: thread.id,
        patient,
        history: history.slice(0, -1),
        userText: parsed.text,
      });

      // 4. Store and send the reply over WhatsApp.
      await this.conversations.addMessage(thread.id, 'assistant', reply);
      await this.ycloud.sendText(patient.phone, reply);
      // SSE events are emitted inside the services above to refresh the UI.
    } catch (e) {
      this.logger.error(
        `Error procesando mensaje entrante: ${e instanceof Error ? e.message : e}`,
      );
    }
  }
}
