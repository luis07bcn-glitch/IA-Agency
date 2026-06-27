import { Module } from '@nestjs/common';
import { VoiceController } from './voice.controller';
import { VoiceService } from './voice.service';
import { VoiceGateway } from './voice.gateway';
import { AgentConfigModule } from '../config/config.module';
import { AgentModule } from '../agent/agent.module';

@Module({
  imports: [AgentConfigModule, AgentModule],
  controllers: [VoiceController],
  providers: [VoiceService, VoiceGateway],
  exports: [VoiceGateway],
})
export class VoiceModule {}
