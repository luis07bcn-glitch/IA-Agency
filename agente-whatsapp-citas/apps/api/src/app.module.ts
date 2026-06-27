import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ScheduleModule } from '@nestjs/schedule';
import { ThrottlerModule, ThrottlerGuard } from '@nestjs/throttler';
import { APP_GUARD } from '@nestjs/core';

import { EventsModule } from './events/events.module';
import { AgentConfigModule } from './config/config.module';
import { PatientsModule } from './patients/patients.module';
import { AppointmentsModule } from './appointments/appointments.module';
import { ConversationsModule } from './conversations/conversations.module';
import { DashboardModule } from './dashboard/dashboard.module';
import { WebhooksModule } from './webhooks/webhooks.module';
import { RemindersModule } from './reminders/reminders.module';
import { SeedModule } from './seed/seed.module';

// Entities (also registered per-module via forFeature).
import { AgentConfig } from './config/agent-config.entity';
import { Patient } from './patients/patient.entity';
import { Appointment } from './appointments/appointment.entity';
import { Conversation } from './conversations/conversation.entity';
import { Message } from './conversations/message.entity';

// Mastra-embedding module: MUST be imported LAST (Mastra mounts catch-all
// routes under /api, so it has to register after all other controllers).
import { VoiceModule } from './voice/voice.module';
import { MetricsModule } from './metrics/metrics.module';
import { DemoModule } from './demo/demo.module';
import { InsightsModule } from './insights/insights.module';
import { AgentModule } from './agent/agent.module';

@Module({
  imports: [
    // envFilePath: the API CWD is apps/api/ so ../../.env points at the monorepo root.
    ConfigModule.forRoot({ isGlobal: true, envFilePath: ['../../.env', '.env'] }),

    TypeOrmModule.forRoot({
      type: 'postgres',
      url:
        process.env.DATABASE_URL ??
        'postgres://citas:cambia-esta-contrasena@localhost:5433/citas',
      entities: [AgentConfig, Patient, Appointment, Conversation, Message],
      // Single-tenant + non-technical deploy: auto-create/update the schema.
      synchronize: true,
    }),

    // Global rate limiting: 100 requests / minute per IP by default.
    ThrottlerModule.forRoot([{ ttl: 60_000, limit: 100 }]),

    ScheduleModule.forRoot(),

    EventsModule,
    AgentConfigModule,
    PatientsModule,
    AppointmentsModule,
    ConversationsModule,
    DashboardModule,
    WebhooksModule,
    RemindersModule,
    SeedModule,
    VoiceModule,
    MetricsModule,
    DemoModule,
    InsightsModule,

    // ---- ALWAYS LAST ----
    AgentModule,
  ],
  providers: [
    {
      provide: APP_GUARD,
      useClass: ThrottlerGuard,
    },
  ],
})
export class AppModule {}
