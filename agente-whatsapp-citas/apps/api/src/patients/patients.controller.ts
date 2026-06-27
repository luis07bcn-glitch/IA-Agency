import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Post,
  Put,
  Query,
} from '@nestjs/common';
import { PatientsService } from './patients.service';
import { CreatePatientDto, UpdatePatientDto } from './dto';

@Controller('patients')
export class PatientsController {
  constructor(private readonly patients: PatientsService) {}

  @Get()
  findAll(@Query('search') search?: string) {
    return this.patients.findAll(search);
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.patients.findOne(id);
  }

  @Post()
  create(@Body() dto: CreatePatientDto) {
    return this.patients.create(dto);
  }

  @Put(':id')
  update(@Param('id') id: string, @Body() dto: UpdatePatientDto) {
    return this.patients.update(id, dto);
  }

  @Delete(':id')
  remove(@Param('id') id: string) {
    return this.patients.remove(id);
  }
}
