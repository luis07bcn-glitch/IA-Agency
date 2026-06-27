import { Controller, Post, Body, Res, Logger, HttpCode } from '@nestjs/common';
import { Response } from 'express';
import { VoiceService } from './voice.service';

/**
 * Twilio calls this endpoint when someone dials the business number.
 * We return TwiML that either:
 *   - Routes the call to ConversationRelay (agent handles it), or
 *   - Forwards directly to staffPhone (human handles it).
 */
@Controller('voice')
export class VoiceController {
  private readonly logger = new Logger('VoiceController');

  constructor(private readonly voice: VoiceService) {}

  /** POST /api/voice/incoming — Twilio webhook for inbound calls */
  @Post('incoming')
  @HttpCode(200)
  async incoming(@Body() body: Record<string, string>, @Res() res: Response) {
    const from = body.From ?? 'unknown';
    this.logger.log(`Llamada entrante de ${from}`);
    const twiml = await this.voice.buildIncomingTwiml(from);
    res.type('text/xml').send(twiml);
  }
}
