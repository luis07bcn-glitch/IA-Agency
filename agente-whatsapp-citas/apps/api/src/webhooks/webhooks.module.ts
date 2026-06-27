import { Module } from '@nestjs/common';
import { WebhooksController } from './webhooks.controller';
import { WebhooksService } from './webhooks.service';
import { YCloudService } from './ycloud.service';
import { PatientsModule } from '../patients/patients.module';
import { ConversationsModule } from '../conversations/conversations.module';
import { AgentModule } from '../agent/agent.module';

@Module({
  imports: [PatientsModule, ConversationsModule, AgentModule],
  controllers: [WebhooksController],
  providers: [WebhooksService, YCloudService],
  exports: [YCloudService],
})
export class WebhooksModule {}
