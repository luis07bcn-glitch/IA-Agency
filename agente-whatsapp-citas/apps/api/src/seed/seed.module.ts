import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AgentConfig } from '../config/agent-config.entity';
import { Patient } from '../patients/patient.entity';
import { Appointment } from '../appointments/appointment.entity';
import { Conversation } from '../conversations/conversation.entity';
import { Message } from '../conversations/message.entity';
import { SeedService } from './seed.service';

@Module({
  imports: [
    TypeOrmModule.forFeature([
      AgentConfig,
      Patient,
      Appointment,
      Conversation,
      Message,
    ]),
  ],
  providers: [SeedService],
})
export class SeedModule {}
