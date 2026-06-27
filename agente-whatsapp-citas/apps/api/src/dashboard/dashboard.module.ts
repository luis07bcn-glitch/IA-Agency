import { Module } from '@nestjs/common';
import { DashboardController } from './dashboard.controller';
import { PatientsModule } from '../patients/patients.module';
import { AppointmentsModule } from '../appointments/appointments.module';
import { ConversationsModule } from '../conversations/conversations.module';
import { AgentConfigModule } from '../config/config.module';

@Module({
  imports: [
    PatientsModule,
    AppointmentsModule,
    ConversationsModule,
    AgentConfigModule,
  ],
  controllers: [DashboardController],
})
export class DashboardModule {}
