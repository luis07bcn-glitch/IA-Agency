import {
  IsArray,
  IsBoolean,
  IsInt,
  IsOptional,
  IsString,
  Max,
  Min,
  ValidateNested,
} from 'class-validator';
import { Type } from 'class-transformer';

export class ServiceDto {
  @IsString()
  name: string;

  @IsInt()
  @Min(5)
  @Max(480)
  durationMin: number;
}

export class IntervalDto {
  @IsString()
  start: string; // "HH:mm"

  @IsString()
  end: string; // "HH:mm"
}

export class DayScheduleDto {
  @IsInt()
  @Min(0)
  @Max(6)
  weekday: number;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => IntervalDto)
  intervals: IntervalDto[];
}

// All fields optional: the UI sends only what it changes (PATCH-style).
// Empty/absent secret fields are IGNORED so they never overwrite a stored secret.
export class UpdateAgentConfigDto {
  @IsOptional() @IsString() centerName?: string;
  @IsOptional() @IsString() description?: string;
  @IsOptional() @IsString() tone?: string;
  @IsOptional() @IsString() timezone?: string;
  @IsOptional() @IsBoolean() enabled?: boolean;

  // --- Voice channel ---
  @IsOptional() @IsBoolean() voiceEnabled?: boolean;
  @IsOptional() @IsString() voiceOverride?: string; // 'auto' | 'agent' | 'staff'
  @IsOptional() @IsString() staffPhone?: string;

  @IsOptional()
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => DayScheduleDto)
  voiceSchedule?: DayScheduleDto[];

  @IsOptional()
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => ServiceDto)
  services?: ServiceDto[];

  @IsOptional()
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => DayScheduleDto)
  schedule?: DayScheduleDto[];

  // Secret. If empty string or omitted, we keep the existing key.
  @IsOptional() @IsString() openrouterApiKey?: string;

  @IsOptional() @IsString() agentModel?: string;

  // External calendar iCal URL. Empty string clears it.
  @IsOptional() @IsString() externalCalendarUrl?: string;

  // ROI / metrics
  @IsOptional() @IsInt() @Min(0) avgTicket?: number;
  @IsOptional() @IsString() ownerPhone?: string;
  @IsOptional() @IsBoolean() dailyDigestEnabled?: boolean;
}
