import { Injectable, Logger } from '@nestjs/common';
import { Cron } from '@nestjs/schedule';
import { MetricsService } from './metrics.service';
import { ConfigService } from '../config/config.service';
import { YCloudService } from '../webhooks/ycloud.service';
import { AppointmentsService } from '../appointments/appointments.service';

/**
 * Sends the business owner a daily summary over WhatsApp.
 * Runs every morning; only fires when dailyDigestEnabled and ownerPhone are set.
 */
@Injectable()
export class DigestService {
  private readonly logger = new Logger('DigestService');

  constructor(
    private readonly metrics: MetricsService,
    private readonly config: ConfigService,
    private readonly ycloud: YCloudService,
    private readonly appointments: AppointmentsService,
  ) {}

  // Every day at 08:00 (server timezone, set via TZ env).
  @Cron('0 8 * * *')
  async sendDailyDigest(): Promise<void> {
    try {
      const cfg = await this.config.getRaw();
      if (!cfg.dailyDigestEnabled || !cfg.ownerPhone) return;

      const text = await this.buildDigestText();
      await this.ycloud.sendText(cfg.ownerPhone, text);
      this.logger.log('Resumen diario enviado al dueño.');
    } catch (e) {
      this.logger.error(`Error enviando resumen diario: ${e instanceof Error ? e.message : e}`);
    }
  }

  /** Builds the digest text. Public so it can be triggered for a test send. */
  async buildDigestText(): Promise<string> {
    const cfg = await this.config.getRaw();
    const todayCount = await this.appointments.countToday();
    const upcoming = await this.appointments.countUpcoming();
    const roi = await this.metrics.roi(7); // last 7 days

    const name = cfg.centerName || 'tu negocio';
    const lines = [
      `☀️ *Buenos días — resumen de ${name}*`,
      ``,
      `📅 Hoy tienes *${todayCount}* cita(s).`,
      `🔜 Próximas citas agendadas: *${upcoming}*`,
      ``,
      `*Últimos 7 días:*`,
      `🤖 El agente reservó *${roi.appointmentsByAgent}* cita(s).`,
      `💬 Mensajes atendidos: *${roi.messagesHandled}*`,
    ];

    if (roi.estimatedRevenue != null) {
      lines.push(`💰 Ingresos estimados generados: *${roi.estimatedRevenue} €*`);
    }
    if (roi.noShow > 0) {
      lines.push(`⚠️ Ausencias (no-show): *${roi.noShow}*`);
    }

    lines.push(``, `¡Que tengas un gran día! 🚀`);
    return lines.join('\n');
  }
}
