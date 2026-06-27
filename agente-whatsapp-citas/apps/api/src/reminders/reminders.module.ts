import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Appointment } from '../appointments/appointment.entity';
import { RemindersService } from './reminders.service';
import { AgentConfigModule } from '../config/config.module';
import { ConversationsModule } from '../conversations/conversations.module';
import { WebhooksModule } from '../webhooks/webhooks.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([Appointment]),
    AgentConfigModule,
    ConversationsModule,
    WebhooksModule, // for YCloudService
  ],
  providers: [RemindersService],
})
export class RemindersModule {}
