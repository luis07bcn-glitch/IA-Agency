import {
  Body,
  Controller,
  Delete,
  Get,
  Post,
  Put,
  Query,
  Req,
  BadRequestException,
} from '@nestjs/common';
import { Request } from 'express';
import { ConfigService } from './config.service';
import { UpdateAgentConfigDto } from './dto';
import { CURATED_MODELS, fetchOpenRouterCatalog } from './openrouter';
// eslint-disable-next-line @typescript-eslint/no-require-imports
const pdfParse = require('pdf-parse');

@Controller('config')
export class ConfigController {
  constructor(private readonly config: ConfigService) {}

  // GET /api/config  -> sanitized config (no secrets, has* booleans)
  @Get()
  async get() {
    return this.config.getSanitized();
  }

  // PUT /api/config  -> update; empty secret fields are ignored
  @Put()
  async update(@Body() dto: UpdateAgentConfigDto) {
    return this.config.update(dto);
  }

  // POST /api/config/knowledge  -> upload PDF or plain text; extracts and stores text
  @Post('knowledge')
  async uploadKnowledge(@Req() req: Request) {
    const chunks: Buffer[] = [];
    await new Promise<void>((resolve, reject) => {
      req.on('data', (chunk: Buffer) => chunks.push(chunk));
      req.on('end', resolve);
      req.on('error', reject);
    });
    const buf = Buffer.concat(chunks);
    if (!buf.length) throw new BadRequestException('No se recibió ningún archivo.');

    const contentType = (req.headers['content-type'] ?? '').toLowerCase();
    let text: string;

    if (contentType.includes('pdf')) {
      const parsed = await pdfParse(buf);
      text = parsed.text as string;
    } else {
      // Treat as plain text (txt, md, etc.)
      text = buf.toString('utf-8');
    }

    if (!text.trim()) throw new BadRequestException('El documento no contiene texto legible.');
    return this.config.saveKnowledgeBase(text);
  }

  // DELETE /api/config/knowledge  -> clear knowledge base
  @Delete('knowledge')
  async clearKnowledge() {
    await this.config.clearKnowledgeBase();
    return { ok: true };
  }

  // GET /api/config/whatsapp-status  -> connection status (no secrets)
  @Get('whatsapp-status')
  async whatsappStatus() {
    return {
      hasApiKey: !!process.env.YCLOUD_API_KEY,
      hasWebhookSecret: !!process.env.YCLOUD_WEBHOOK_SECRET,
      phoneNumber: process.env.YCLOUD_WHATSAPP_NUMBER || null,
      webhookUrl: `${process.env.PUBLIC_URL || '(configura PUBLIC_URL en .env)'}/api/webhooks/ycloud`,
    };
  }

  // GET /api/config/models           -> curated shortlist
  // GET /api/config/models?all=true  -> full live OpenRouter catalog
  @Get('models')
  async models(@Query('all') all?: string) {
    if (all === 'true') {
      try {
        return { models: await fetchOpenRouterCatalog(), source: 'live' };
      } catch {
        // Fall back to curated if the catalog is unreachable.
        return { models: CURATED_MODELS, source: 'curated-fallback' };
      }
    }
    return { models: CURATED_MODELS, source: 'curated' };
  }
}
