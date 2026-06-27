import {
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Between, LessThan, MoreThan, Repository } from 'typeorm';
import { Appointment } from './appointment.entity';
import { CreateAppointmentDto, UpdateAppointmentDto } from './dto';
import { Patient } from '../patients/patient.entity';
import { ConfigService } from '../config/config.service';
import { EventsService } from '../events/events.service';
import { ExternalCalendarService } from './external-calendar.service';
import {
  dateKeyInTz,
  formatHuman,
  parseZoned,
  timeInTz,
  weekdayInTz,
} from '../common/timezone';

export interface Slot {
  startsAt: string; // ISO UTC
  label: string; // "10:00" in center tz
}

@Injectable()
export class AppointmentsService {
  constructor(
    @InjectRepository(Appointment)
    private readonly repo: Repository<Appointment>,
    @InjectRepository(Patient)
    private readonly patients: Repository<Patient>,
    private readonly config: ConfigService,
    private readonly events: EventsService,
    private readonly externalCalendar: ExternalCalendarService,
  ) {}

  // ---- Queries -----------------------------------------------------------

  /** Appointments overlapping the [from, to] window (for the calendar). */
  async findRange(fromIso: string, toIso: string): Promise<Appointment[]> {
    return this.repo.find({
      where: { startsAt: Between(new Date(fromIso), new Date(toIso)) },
      order: { startsAt: 'ASC' },
    });
  }

  async findForPatient(patientId: string): Promise<Appointment[]> {
    return this.repo.find({
      where: { patientId },
      order: { startsAt: 'DESC' },
    });
  }

  async findOne(id: string): Promise<Appointment> {
    const appt = await this.repo.findOne({ where: { id } });
    if (!appt) throw new NotFoundException('Cita no encontrada');
    return appt;
  }

  async countToday(): Promise<number> {
    const cfg = await this.config.getRaw();
    const now = new Date();
    const key = dateKeyInTz(now, cfg.timezone);
    const dayStart = parseZoned(key, '00:00', cfg.timezone);
    const dayEnd = new Date(dayStart.getTime() + 24 * 3600 * 1000);
    return this.repo.count({
      where: {
        startsAt: Between(dayStart, dayEnd),
        status: 'scheduled' as const,
      },
    });
  }

  async countUpcoming(): Promise<number> {
    return this.repo.count({
      where: { startsAt: MoreThan(new Date()), status: 'scheduled' as const },
    });
  }

  // ---- Availability ------------------------------------------------------

  private serviceDuration(serviceName: string, services: { name: string; durationMin: number }[]): number {
    const svc = services.find(
      (s) => s.name.toLowerCase() === serviceName.toLowerCase(),
    );
    return svc?.durationMin ?? 45; // sensible default
  }

  /** Free slots for a service on a given date ("YYYY-MM-DD") in center tz. */
  async availability(serviceName: string, dateStr: string): Promise<Slot[]> {
    const cfg = await this.config.getRaw();
    const tz = cfg.timezone;
    const duration = this.serviceDuration(serviceName, cfg.services ?? []);

    // Which weekday is this date in the center tz?
    const dayProbe = parseZoned(dateStr, '12:00', tz);
    const weekday = weekdayInTz(dayProbe, tz);
    const daySchedule = (cfg.schedule ?? []).find((d) => d.weekday === weekday);
    if (!daySchedule || daySchedule.intervals.length === 0) return [];

    // Existing scheduled appointments on that day.
    const dayStart = parseZoned(dateStr, '00:00', tz);
    const dayEnd = new Date(dayStart.getTime() + 24 * 3600 * 1000);
    const existing = await this.repo.find({
      where: {
        startsAt: Between(dayStart, dayEnd),
        status: 'scheduled' as const,
      },
    });
    const busy = existing.map((a) => ({
      start: a.startsAt.getTime(),
      end: a.endsAt.getTime(),
    }));

    // Fetch external calendar busy ranges (TheFork, Google Calendar, etc.)
    const externalBusy = cfg.externalCalendarUrl
      ? await this.externalCalendar.getBusyRanges(cfg.externalCalendarUrl, dayStart)
      : [];

    const now = Date.now();
    const slots: Slot[] = [];
    const stepMs = duration * 60 * 1000;

    for (const interval of daySchedule.intervals) {
      let cursor = parseZoned(dateStr, interval.start, tz).getTime();
      const limit = parseZoned(dateStr, interval.end, tz).getTime();
      while (cursor + stepMs <= limit) {
        const slotStart = new Date(cursor);
        const slotEnd = new Date(cursor + stepMs);
        const overlapsCrm = busy.some((b) => cursor < b.end && cursor + stepMs > b.start);
        const overlapsExternal = this.externalCalendar.isSlotBusy(slotStart, slotEnd, externalBusy);
        if (!overlapsCrm && !overlapsExternal && cursor > now) {
          slots.push({
            startsAt: slotStart.toISOString(),
            label: timeInTz(slotStart, tz),
          });
        }
        cursor += stepMs;
      }
    }
    return slots;
  }

  private async assertSlotFree(
    startsAt: Date,
    endsAt: Date,
    ignoreId?: string,
  ): Promise<void> {
    const overlapping = await this.repo.find({
      where: {
        status: 'scheduled' as const,
        startsAt: LessThan(endsAt),
        endsAt: MoreThan(startsAt),
      },
    });
    const clash = overlapping.find((a) => a.id !== ignoreId);
    if (clash) {
      throw new BadRequestException('Ese horario ya esta ocupado');
    }
  }

  // ---- Mutations ---------------------------------------------------------

  async create(
    dto: CreateAppointmentDto,
    source: 'manual' | 'agent' = 'manual',
  ): Promise<Appointment> {
    const patient = await this.patients.findOne({
      where: { id: dto.patientId },
    });
    if (!patient) throw new NotFoundException('Paciente no encontrado');

    const cfg = await this.config.getRaw();
    const duration = this.serviceDuration(dto.serviceName, cfg.services ?? []);
    const startsAt = new Date(dto.startsAt);
    const endsAt = new Date(startsAt.getTime() + duration * 60 * 1000);

    await this.assertSlotFree(startsAt, endsAt);

    const appt = this.repo.create({
      patientId: dto.patientId,
      serviceName: dto.serviceName,
      startsAt,
      endsAt,
      status: 'scheduled',
      source,
      notes: dto.notes ?? null,
    });
    const saved = await this.repo.save(appt);
    this.events.emit('appointment.changed', { id: saved.id });
    return this.findOne(saved.id);
  }

  async update(id: string, dto: UpdateAppointmentDto): Promise<Appointment> {
    const appt = await this.findOne(id);
    const cfg = await this.config.getRaw();

    if (dto.serviceName !== undefined) appt.serviceName = dto.serviceName;
    if (dto.notes !== undefined) appt.notes = dto.notes || null;
    if (dto.status !== undefined) appt.status = dto.status;

    if (dto.startsAt !== undefined) {
      const duration = this.serviceDuration(appt.serviceName, cfg.services ?? []);
      appt.startsAt = new Date(dto.startsAt);
      appt.endsAt = new Date(appt.startsAt.getTime() + duration * 60 * 1000);
      appt.reminder24Sent = false;
      appt.reminder2Sent = false;
      await this.assertSlotFree(appt.startsAt, appt.endsAt, appt.id);
    }

    const saved = await this.repo.save(appt);
    this.events.emit('appointment.changed', { id });
    return this.findOne(saved.id);
  }

  async cancel(id: string): Promise<Appointment> {
    const appt = await this.findOne(id);
    appt.status = 'cancelled';
    const saved = await this.repo.save(appt);
    this.events.emit('appointment.changed', { id });
    return saved;
  }

  async remove(id: string): Promise<void> {
    const appt = await this.findOne(id);
    await this.repo.remove(appt);
    this.events.emit('appointment.changed', { id });
  }

  /** Helper used by the agent tools: a readable confirmation line. */
  async describe(appt: Appointment): Promise<string> {
    const cfg = await this.config.getRaw();
    return `${appt.serviceName} el ${formatHuman(appt.startsAt, cfg.timezone)}`;
  }
}
