import { Body, Controller, Get, Post, Query } from '@nestjs/common';
import { IsInt, IsOptional, IsString, Max, MaxLength, Min, MinLength } from 'class-validator';
import { Type } from 'class-transformer';
import { InsightsService } from './insights.service';

class AskDto {
  @IsString()
  @MinLength(3)
  @MaxLength(500)
  question: string;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(365)
  days?: number;
}

@Controller('insights')
export class InsightsController {
  constructor(private readonly insights: InsightsService) {}

  // GET /api/insights/suggestions -> starter questions for the UI
  @Get('suggestions')
  suggestions() {
    return { questions: this.insights.suggestions() };
  }

  // POST /api/insights/ask -> answer a free-form question from real data
  @Post('ask')
  ask(@Body() dto: AskDto) {
    return this.insights.ask(dto.question, dto.days ?? 30);
  }

  // GET /api/insights/report?days=30 -> structured business report
  @Get('report')
  report(@Query('days') days?: string) {
    const d = Number(days);
    return this.insights.report(Number.isFinite(d) && d > 0 ? Math.min(d, 365) : 30);
  }
}
