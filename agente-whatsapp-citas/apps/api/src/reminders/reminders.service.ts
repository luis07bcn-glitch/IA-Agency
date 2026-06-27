import { Injectable, Logger } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { InjectRepository } from '@nestjs/typeorm';
import { Between, LessThan, Repository } from 'typeorm';
import { Appointment } from '../appointments/appointment.entity';
import { ConfigService } from '../config/config.service';
import { ConversationsService } from '../conversations/conversations.service';
import { YCloudService } from '../webhooks/ycloud.service';
import { formatHuman, timeInTz } from '../common/timezone';

/**
 * Anti-no-show reminders. Runs every 15 minutes:
 *   - 24h before the appointment: reminder + confirmation request.
 *   - 2h before: short confirmation reminder.
 *   - after a no-show (status = no_show): one recovery message inviting to rebook.
 *
 * Every sent reminder is also stored in the patient's conversation thread so it
 * shows up in the inbox.
 */
@Injectable()
export class RemindersService {
  private readonly logger = new Logger('RemindersService');

  constructor(
    @InjectRepository(Appointment)
    private readonly repo: Repository<Appointment>,
    private readonly config: ConfigService,
    private readonly conversations: ConversationsService,
    private readonly ycloud: YCloudService,
  ) {}

  @Cron(CronExpression.EVERY_5_MINUTES)
  async tick(): Promise<void> {
    try {
      await this.send24hReminders();
      await this.send2hReminders();
      await this.sendNoShowRecovery();
    } catch (e) {
      this.logger.error(
        `Error en el ciclo de recordatorios: ${e instanceof Error ? e.message : e}`,
      );
    }
  }

  private async deliver(appt: Appointment, text: string): Promise<void> {
    const patient = appt.patient;
    if (!patient?.phone) return;
    await this.ycloud.sendText(patient.phone, text);
    const thread = await this.conversations.getOrCreateWhatsappThread(
      patient.phone,
      patient.id,
      patient.name,
    );
    await this.conversations.addMessage(thread.id, 'assistant', text);
  }

  private async send24hReminders(): Promise<void> {
    const cfg = await this.config.getRaw();
    const now = Date.now();
    const from = new Date(now + 23 * 3600 * 1000);
    const to = new Date(now + 24 * 3600 * 1000);
    const due = await this.repo.find({
      where: {
        status: 'scheduled',
        reminder24Sent: false,
        startsAt: Between(from, to),
      },
    });
    for (const appt of due) {
      const text = `¡Hola ${appt.patient.name.split(' ')[0]}! Te recordamos tu cita en ${cfg.centerName}: ${appt.serviceName} mañana ${formatHuman(appt.startsAt, cfg.timezone)}. Responde SÍ para confirmar o escríbenos si necesitas cambiarla. ¡Te esperamos!`;
      await this.deliver(appt, text);
      appt.reminder24Sent = true;
      await this.repo.save(appt);
    }
  }

  private async send2hReminders(): Promise<void> {
    const cfg = await this.config.getRaw();
    const now = Date.now();
    const from = new Date(now + 1.5 * 3600 * 1000);
    const to = new Date(now + 2 * 3600 * 1000);
    const due = await this.repo.find({
      where: {
        status: 'scheduled',
        reminder2Sent: false,
        startsAt: Between(from, to),
      },
    });
    for (const appt of due) {
      const text = `Recordatorio: hoy a las ${timeInTz(appt.startsAt, cfg.timezone)} tienes tu cita de ${appt.serviceName} en ${cfg.centerName}. ¡Nos vemos en un rato!`;
      await this.deliver(appt, text);
      appt.reminder2Sent = true;
      await this.repo.save(appt);
    }
  }

  private async sendNoShowRecovery(): Promise<void> {
    const cfg = await this.config.getRaw();
    const due = await this.repo.find({
      where: {
        status: 'no_show',
        noShowRecoverySent: false,
        startsAt: LessThan(new Date()),
      },
    });
    for (const appt of due) {
      const text = `Hola ${appt.patient.name.split(' ')[0]}, vimos que no pudiste venir a tu cita de ${appt.serviceName}. Sin problema 🙂 ¿Quieres que busquemos un nuevo hueco que te venga mejor? Solo dinos cuándo.`;
      await this.deliver(appt, text);
      appt.noShowRecoverySent = true;
      await this.repo.save(appt);
    }
  }
}
