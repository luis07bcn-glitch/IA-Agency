import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Appointment } from './appointment.entity';
import { Patient } from '../patients/patient.entity';
import { AppointmentsController } from './appointments.controller';
import { AppointmentsService } from './appointments.service';
import { ExternalCalendarService } from './external-calendar.service';
import { AgentConfigModule } from '../config/config.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([Appointment, Patient]),
    AgentConfigModule,
  ],
  controllers: [AppointmentsController],
  providers: [AppointmentsService, ExternalCalendarService],
  exports: [AppointmentsService],
})
export class AppointmentsModule {}
