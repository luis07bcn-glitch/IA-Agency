import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AgentConfig } from './agent-config.entity';
import { ConfigController } from './config.controller';
import { ConfigService } from './config.service';

@Module({
  imports: [TypeOrmModule.forFeature([AgentConfig])],
  controllers: [ConfigController],
  providers: [ConfigService],
  exports: [ConfigService],
})
export class AgentConfigModule {}
