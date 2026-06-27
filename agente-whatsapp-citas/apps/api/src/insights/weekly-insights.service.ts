import { Injectable, Logger } from '@nestjs/common';
import { Cron } from '@nestjs/schedule';
import { InsightsService } from './insights.service';
import { ConfigService } from '../config/config.service';
import { YCloudService } from '../webhooks/ycloud.service';

/**
 * Sends the business owner a weekly AI-generated insights report via WhatsApp.
 * Fires every Monday at 08:30 (server timezone, set via TZ env).
 * Only fires when ownerPhone is configured.
 */
@Injectable()
export class WeeklyInsightsService {
  private readonly logger = new Logger('WeeklyInsightsService');

  constructor(
    private readonly insights: InsightsService,
    private readonly config: ConfigService,
    private readonly ycloud: YCloudService,
  ) {}

  @Cron('30 8 * * 1')
  async sendWeeklyInsights(): Promise<void> {
    try {
      const cfg = await this.config.getRaw();
      if (!cfg.ownerPhone) return;

      const text = await this.buildWeeklyText();
      await this.ycloud.sendText(cfg.ownerPhone, text);
      this.logger.log('Informe semanal de insights enviado al dueño.');
    } catch (e) {
      this.logger.error(`Error enviando informe semanal: ${e instanceof Error ? e.message : e}`);
    }
  }

  /** Builds the WhatsApp-formatted insights report. Public for manual test sends. */
  async buildWeeklyText(): Promise<string> {
    const cfg = await this.config.getRaw();
    const name = cfg.centerName || 'tu negocio';

    const report = await this.insights.report(7);

    const lines: string[] = [
      `🧠 *Informe semanal — ${name}*`,
      `📊 _${report.basedOn.conversations} conversación(es) analizadas · últimos 7 días_`,
      ``,
      `*${report.summary}*`,
    ];

    if (report.findings.length === 0) {
      lines.push(``, `Aún no hay suficientes conversaciones para sacar conclusiones. Cuando el asistente atienda más clientes por WhatsApp, aquí verás los patrones clave.`);
    } else {
      lines.push(``);
      for (const f of report.findings.slice(0, 5)) {
        lines.push(`${f.emoji} *${f.title}*`);
        if (f.detail) lines.push(`${f.detail}`);
        if (f.action) lines.push(`↳ 💡 ${f.action}`);
        lines.push(``);
      }
    }

    lines.push(`Ver el informe completo en tu panel de gestión.`);
    return lines.join('\n');
  }
}
