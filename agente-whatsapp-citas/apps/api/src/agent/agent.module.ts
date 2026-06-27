import { Module } from '@nestjs/common';
import { AgentService } from './agent.service';
import { PlaygroundController } from './playground.controller';
import { AgentConfigModule } from '../config/config.module';
import { AppointmentsModule } from '../appointments/appointments.module';
import { ConversationsModule } from '../conversations/conversations.module';
import { PatientsModule } from '../patients/patients.module';

// IMPORTANT: this module embeds Mastra. It MUST be the LAST module imported in
// app.module.ts because Mastra can mount catch-all routes under /api.
@Module({
  imports: [
    AgentConfigModule,
    AppointmentsModule,
    ConversationsModule,
    PatientsModule,
  ],
  controllers: [PlaygroundController],
  providers: [AgentService],
  exports: [AgentService],
})
export class AgentModule {}
