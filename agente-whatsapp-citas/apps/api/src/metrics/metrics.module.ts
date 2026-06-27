import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Appointment } from '../appointments/appointment.entity';
import { Conversation } from '../conversations/conversation.entity';
import { Message } from '../conversations/message.entity';
import { MetricsService } from './metrics.service';
import { DigestService } from './digest.service';
import { WeeklyInsightsService } from '../insights/weekly-insights.service';
import { MetricsController } from './metrics.controller';
import { AgentConfigModule } from '../config/config.module';
import { AppointmentsModule } from '../appointments/appointments.module';
import { WebhooksModule } from '../webhooks/webhooks.module';
import { InsightsModule } from '../insights/insights.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([Appointment, Conversation, Message]),
    AgentConfigModule,
    AppointmentsModule,
    WebhooksModule,
    InsightsModule,
  ],
  controllers: [MetricsController],
  providers: [MetricsService, DigestService, WeeklyInsightsService],
})
export class MetricsModule {}
