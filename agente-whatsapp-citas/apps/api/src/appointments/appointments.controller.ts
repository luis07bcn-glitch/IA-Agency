import {
  BadRequestException,
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Post,
  Put,
  Query,
} from '@nestjs/common';
import { AppointmentsService } from './appointments.service';
import { CreateAppointmentDto, UpdateAppointmentDto } from './dto';

@Controller('appointments')
export class AppointmentsController {
  constructor(private readonly appointments: AppointmentsService) {}

  // GET /api/appointments?from=ISO&to=ISO  (calendar window)
  @Get()
  findRange(@Query('from') from?: string, @Query('to') to?: string) {
    if (!from || !to) {
      throw new BadRequestException('Faltan los parametros from y to');
    }
    return this.appointments.findRange(from, to);
  }

  // GET /api/appointments/availability?service=...&date=YYYY-MM-DD
  @Get('availability')
  availability(
    @Query('service') service: string,
    @Query('date') date: string,
  ) {
    if (!service || !date) {
      throw new BadRequestException('Faltan service y date');
    }
    return this.appointments.availability(service, date);
  }

  @Post()
  create(@Body() dto: CreateAppointmentDto) {
    return this.appointments.create(dto, 'manual');
  }

  @Put(':id')
  update(@Param('id') id: string, @Body() dto: UpdateAppointmentDto) {
    return this.appointments.update(id, dto);
  }

  @Delete(':id')
  remove(@Param('id') id: string) {
    return this.appointments.remove(id);
  }
}
