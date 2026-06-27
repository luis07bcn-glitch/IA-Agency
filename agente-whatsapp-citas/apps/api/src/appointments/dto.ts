import {
  IsDateString,
  IsIn,
  IsOptional,
  IsString,
  IsUUID,
} from 'class-validator';
import type { AppointmentStatus } from './appointment.entity';

export class CreateAppointmentDto {
  @IsUUID()
  patientId: string;

  @IsString()
  serviceName: string;

  // ISO datetime (UTC) for the start. End is derived from the service duration.
  @IsDateString()
  startsAt: string;

  @IsOptional()
  @IsString()
  notes?: string;
}

export class UpdateAppointmentDto {
  @IsOptional() @IsString() serviceName?: string;
  @IsOptional() @IsDateString() startsAt?: string;
  @IsOptional()
  @IsIn(['scheduled', 'completed', 'cancelled', 'no_show'])
  status?: AppointmentStatus;
  @IsOptional() @IsString() notes?: string;
}
