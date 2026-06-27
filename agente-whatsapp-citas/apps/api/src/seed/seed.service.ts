import { Injectable, Logger, OnApplicationBootstrap } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { AgentConfig, AGENT_CONFIG_ID } from '../config/agent-config.entity';
import { Patient } from '../patients/patient.entity';
import { Appointment } from '../appointments/appointment.entity';
import { Conversation } from '../conversations/conversation.entity';
import { Message } from '../conversations/message.entity';
import { parseZoned, dateKeyInTz } from '../common/timezone';

const TZ = 'Europe/Madrid';

@Injectable()
export class SeedService implements OnApplicationBootstrap {
  private readonly logger = new Logger('SeedService');

  constructor(
    @InjectRepository(AgentConfig)
    private readonly configRepo: Repository<AgentConfig>,
    @InjectRepository(Patient)
    private readonly patientRepo: Repository<Patient>,
    @InjectRepository(Appointment)
    private readonly apptRepo: Repository<Appointment>,
    @InjectRepository(Conversation)
    private readonly convRepo: Repository<Conversation>,
    @InjectRepository(Message)
    private readonly msgRepo: Repository<Message>,
  ) {}

  async onApplicationBootstrap(): Promise<void> {
    if (process.env.SEED_DEMO_DATA === 'false') {
      this.logger.log('SEED_DEMO_DATA=false: no se cargan datos de ejemplo.');
      return;
    }
    // Idempotent: only seed when there are no patients yet (fresh DB).
    const patientCount = await this.patientRepo.count();
    if (patientCount > 0) return;

    this.logger.log('Base de datos vacía: cargando datos de ejemplo...');
    await this.seedConfig();
    await this.seedPatientsAndAppointments();
    this.logger.log('Datos de ejemplo cargados.');
  }

  private async seedConfig(): Promise<void> {
    const cfg = this.configRepo.create({
      id: AGENT_CONFIG_ID,
      centerName: 'Fisioterapia Bienestar',
      description:
        'Centro de fisioterapia y rehabilitación. Atendemos lesiones, dolores y recuperación funcional.',
      tone: 'cercano y profesional',
      timezone: TZ,
      enabled: true,
      agentModel: process.env.AGENT_MODEL || 'anthropic/claude-3.5-sonnet',
      openrouterApiKey: null,
      services: [
        { name: 'Primera valoración', durationMin: 45 },
        { name: 'Sesión de fisioterapia', durationMin: 45 },
        { name: 'Punción seca', durationMin: 30 },
        { name: 'Masaje terapéutico', durationMin: 60 },
        { name: 'Rehabilitación post-operatoria', durationMin: 45 },
        { name: 'Fisioterapia deportiva', durationMin: 45 },
      ],
      // L-V 9-14 y 16-20; sábado 9-13.
      schedule: [
        { weekday: 1, intervals: [{ start: '09:00', end: '14:00' }, { start: '16:00', end: '20:00' }] },
        { weekday: 2, intervals: [{ start: '09:00', end: '14:00' }, { start: '16:00', end: '20:00' }] },
        { weekday: 3, intervals: [{ start: '09:00', end: '14:00' }, { start: '16:00', end: '20:00' }] },
        { weekday: 4, intervals: [{ start: '09:00', end: '14:00' }, { start: '16:00', end: '20:00' }] },
        { weekday: 5, intervals: [{ start: '09:00', end: '14:00' }, { start: '16:00', end: '20:00' }] },
        { weekday: 6, intervals: [{ start: '09:00', end: '13:00' }] },
        { weekday: 0, intervals: [] },
      ],
    });
    await this.configRepo.save(cfg);
  }

  private dayOffsetKey(offsetDays: number): string {
    const d = new Date(Date.now() + offsetDays * 24 * 3600 * 1000);
    return dateKeyInTz(d, TZ);
  }

  private async seedPatientsAndAppointments(): Promise<void> {
    const patientsData = [
      { name: 'María García', phone: '+34600111222', email: 'maria.garcia@example.com', notes: 'Dolor lumbar recurrente.' },
      { name: 'Juan Martínez', phone: '+34600333444', email: null, notes: 'Recuperación de rodilla (post-operatorio).' },
      { name: 'Lucía Fernández', phone: '+34600555666', email: 'lucia.f@example.com', notes: 'Tendinitis de hombro.' },
      { name: 'Carlos Ruiz', phone: '+34600777888', email: null, notes: 'Deportista, sobrecarga muscular.' },
    ];

    const patients: Patient[] = [];
    for (const p of patientsData) {
      patients.push(await this.patientRepo.save(this.patientRepo.create(p)));
    }

    // Appointments: a couple past and a couple upcoming.
    const make = (
      patient: Patient,
      service: string,
      durationMin: number,
      dateKey: string,
      time: string,
      status: Appointment['status'],
    ) => {
      const startsAt = parseZoned(dateKey, time, TZ);
      const endsAt = new Date(startsAt.getTime() + durationMin * 60000);
      return this.apptRepo.create({
        patientId: patient.id,
        serviceName: service,
        startsAt,
        endsAt,
        status,
        source: 'manual',
        notes: null,
      });
    };

    await this.apptRepo.save([
      make(patients[0], 'Sesión de fisioterapia', 45, this.dayOffsetKey(-7), '10:00', 'completed'),
      make(patients[1], 'Rehabilitación post-operatoria', 45, this.dayOffsetKey(-3), '17:00', 'completed'),
      make(patients[2], 'Primera valoración', 45, this.dayOffsetKey(-2), '11:00', 'no_show'),
      make(patients[0], 'Sesión de fisioterapia', 45, this.dayOffsetKey(1), '10:00', 'scheduled'),
      make(patients[3], 'Fisioterapia deportiva', 45, this.dayOffsetKey(2), '18:00', 'scheduled'),
      make(patients[1], 'Rehabilitación post-operatoria', 45, this.dayOffsetKey(4), '17:00', 'scheduled'),
    ]);

    // Two example WhatsApp conversations.
    await this.seedConversation(patients[2], [
      { role: 'user', text: 'Hola, me molesta el hombro desde hace días, ¿tenéis hueco esta semana?' },
      { role: 'assistant', text: 'Hola Lucía, siento que tengas molestias en el hombro. Lo mejor es que un fisioterapeuta te valore en persona. ¿Te reservo una Primera valoración? Tengo huecos esta semana por la mañana y por la tarde.' },
      { role: 'user', text: 'Mejor por la tarde.' },
      { role: 'assistant', text: 'Perfecto. ¿Te viene bien el jueves a las 17:00 para la Primera valoración?' },
    ]);

    await this.seedConversation(patients[3], [
      { role: 'user', text: 'Buenas, quería cambiar mi cita de fisioterapia deportiva.' },
      { role: 'assistant', text: '¡Hola Carlos! Claro. ¿Para qué día te gustaría cambiarla?' },
    ]);
  }

  private async seedConversation(
    patient: Patient,
    messages: { role: 'user' | 'assistant'; text: string }[],
  ): Promise<void> {
    const now = Date.now();
    const conv = await this.convRepo.save(
      this.convRepo.create({
        patientId: patient.id,
        channel: 'whatsapp',
        phone: patient.phone,
        title: patient.name,
        lastMessageAt: new Date(now),
      }),
    );
    let i = 0;
    for (const m of messages) {
      await this.msgRepo.save(
        this.msgRepo.create({
          conversationId: conv.id,
          role: m.role,
          text: m.text,
          createdAt: new Date(now - (messages.length - i) * 60000),
        }),
      );
      i++;
    }
  }
}
