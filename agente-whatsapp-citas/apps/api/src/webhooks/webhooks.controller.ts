import {
  Controller,
  Headers,
  HttpCode,
  Post,
  Req,
  UnauthorizedException,
} from '@nestjs/common';
import { Throttle } from '@nestjs/throttler';
import type { RawBodyRequest } from '@nestjs/common';
import type { Request } from 'express';
import { YCloudService } from './ycloud.service';
import { WebhooksService } from './webhooks.service';

@Controller('webhooks')
export class WebhooksController {
  constructor(
    private readonly ycloud: YCloudService,
    private readonly webhooks: WebhooksService,
  ) {}

  // POST /api/webhooks/ycloud  (single webhook: one agent, no :agentKey)
  // This is the ONLY public endpoint. It is fail-closed: without a configured
  // webhook secret, every request is rejected.
  @Post('ycloud')
  @HttpCode(200)
  // Allow a higher rate for the webhook (real traffic) but still bounded.
  @Throttle({ default: { limit: 120, ttl: 60_000 } })
  async ycloudWebhook(
    @Req() req: RawBodyRequest<Request>,
    @Headers('x-ycloud-signature') signature?: string,
  ) {
    const ok = this.ycloud.verifySignature(req.rawBody, signature);
    if (!ok) {
      throw new UnauthorizedException('Firma no válida');
    }

    // Respond 200 fast; process in the background.
    void this.webhooks.handleInbound(req.body);
    return { received: true };
  }
}
