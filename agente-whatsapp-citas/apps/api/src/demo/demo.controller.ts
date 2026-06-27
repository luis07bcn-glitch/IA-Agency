import { Body, Controller, Get, Post } from '@nestjs/common';
import {
  IsArray,
  IsObject,
  IsOptional,
  IsString,
  MaxLength,
  MinLength,
} from 'class-validator';
import { DemoService, DemoConfig } from './demo.service';

class BuildDto {
  @IsString()
  @MinLength(1)
  @MaxLength(120)
  name: string;

  @IsOptional()
  @IsString()
  @MaxLength(120)
  city?: string;
}

class ChatDto {
  @IsObject()
  config: DemoConfig;

  @IsOptional()
  @IsString()
  knowledgeBase?: string;

  @IsOptional()
  @IsArray()
  history?: { role: 'user' | 'assistant'; content: string }[];

  @IsString()
  @MinLength(1)
  @MaxLength(2000)
  message: string;
}

class ApplyDto {
  @IsObject()
  config: DemoConfig;

  @IsOptional()
  @IsString()
  knowledgeBase?: string;
}

@Controller('demo')
export class DemoController {
  constructor(private readonly demo: DemoService) {}

  // GET /api/demo/status -> whether the Places key is configured
  @Get('status')
  status() {
    return { configured: this.demo.isConfigured };
  }

  // POST /api/demo/build -> look up a business and build a ready agent
  @Post('build')
  async build(@Body() dto: BuildDto) {
    return this.demo.build(dto.name, dto.city ?? '');
  }

  // POST /api/demo/chat -> talk to the generated (not yet applied) agent
  @Post('chat')
  async chat(@Body() dto: ChatDto) {
    const history = (dto.history ?? [])
      .filter((m) => (m?.role === 'user' || m?.role === 'assistant') && typeof m?.content === 'string')
      .slice(-12)
      .map((m) => ({ role: m.role, content: m.content.slice(0, 2000) }));
    const reply = await this.demo.chat(dto.config, dto.knowledgeBase ?? '', history, dto.message);
    return { reply };
  }

  // POST /api/demo/apply -> persist the generated config as the live agent
  @Post('apply')
  async apply(@Body() dto: ApplyDto) {
    return this.demo.apply(dto.config, dto.knowledgeBase ?? '');
  }
}
