import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Conversation } from '../conversations/conversation.entity';
import { Message } from '../conversations/message.entity';
import { Appointment } from '../appointments/appointment.entity';
import { AgentConfigModule } from '../config/config.module';
import { InsightsService } from './insights.service';
import { InsightsController } from './insights.controller';

@Module({
  imports: [
    TypeOrmModule.forFeature([Conversation, Message, Appointment]),
    AgentConfigModule,
  ],
  controllers: [InsightsController],
  providers: [InsightsService],
  exports: [InsightsService],
})
export class InsightsModule {}
