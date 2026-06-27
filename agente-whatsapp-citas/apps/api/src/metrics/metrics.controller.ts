import { Controller, Get, HttpCode, Post, Query, BadRequestException } from '@nestjs/common';
import { MetricsService } from './metrics.service';
import { DigestService } from './digest.service';
import { WeeklyInsightsService } from '../insights/weekly-insights.service';
import { ConfigService } from '../config/config.service';
import { YCloudService } from '../webhooks/ycloud.service';

@Controller('metrics')
export class MetricsController {
  constructor(
    private readonly metrics: MetricsService,
    private readonly digest: DigestService,
    private readonly weekly: WeeklyInsightsService,
    private readonly config: ConfigService,
    private readonly ycloud: YCloudService,
  ) {}

  // GET /api/metrics/roi?days=30
  @Get('roi')
  async roi(@Query('days') days?: string) {
    const periodDays = Math.min(Math.max(Number(days) || 30, 1), 365);
    return this.metrics.roi(periodDays);
  }

  // GET /api/metrics/digest-preview -> the text that would be sent (for the UI)
  @Get('digest-preview')
  async digestPreview() {
    return { text: await this.digest.buildDigestText() };
  }

  // POST /api/metrics/digest-test -> send the digest now to the owner phone
  @Post('digest-test')
  async digestTest() {
    const cfg = await this.config.getRaw();
    if (!cfg.ownerPhone) {
      throw new BadRequestException('Configura el teléfono del dueño primero.');
    }
    const text = await this.digest.buildDigestText();
    await this.ycloud.sendText(cfg.ownerPhone, text);
    return { ok: true, sentTo: cfg.ownerPhone };
  }

  // POST /api/metrics/weekly-insights-send -> manually trigger the weekly insights report
  @Post('weekly-insights-send')
  @HttpCode(200)
  async weeklyInsightsSend() {
    await this.weekly.sendWeeklyInsights();
    return { sent: true };
  }
}
