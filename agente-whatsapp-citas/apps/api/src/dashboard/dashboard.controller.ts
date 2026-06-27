import { Controller, Get } from '@nestjs/common';
import { PatientsService } from '../patients/patients.service';
import { AppointmentsService } from '../appointments/appointments.service';
import { ConversationsService } from '../conversations/conversations.service';
import { ConfigService } from '../config/config.service';

@Controller('dashboard')
export class DashboardController {
  constructor(
    private readonly patients: PatientsService,
    private readonly appointments: AppointmentsService,
    private readonly conversations: ConversationsService,
    private readonly config: ConfigService,
  ) {}

  // GET /api/dashboard -> metrics + recent conversations for the home screen
  @Get()
  async metrics() {
    const cfg = await this.config.getSanitized();
    const [patients, appointmentsToday, upcoming, recent] = await Promise.all([
      this.patients.count(),
      this.appointments.countToday(),
      this.appointments.countUpcoming(),
      this.conversations.recent(6),
    ]);

    return {
      patients,
      appointmentsToday,
      upcoming,
      agent: {
        enabled: cfg.enabled,
        hasApiKey: cfg.hasOpenrouterApiKey,
        model: cfg.agentModel,
        centerName: cfg.centerName,
      },
      recentConversations: recent.map((c) => ({
        id: c.id,
        title: c.title,
        channel: c.channel,
        lastMessageAt: c.lastMessageAt,
      })),
    };
  }
}
