import { Module } from '@nestjs/common';
import { AgentConfigModule } from '../config/config.module';
import { DemoController } from './demo.controller';
import { DemoService } from './demo.service';
import { PlacesService } from './places.service';
import { WebScraperService } from './web-scraper.service';

@Module({
  imports: [AgentConfigModule],
  controllers: [DemoController],
  providers: [DemoService, PlacesService, WebScraperService],
})
export class DemoModule {}
