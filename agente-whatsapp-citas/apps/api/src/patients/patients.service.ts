import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { ILike, Repository } from 'typeorm';
import { Patient } from './patient.entity';
import { CreatePatientDto, UpdatePatientDto } from './dto';
import { EventsService } from '../events/events.service';

// Normalizes phones to E.164-ish (+34...) so WhatsApp upserts match.
export function normalizePhone(raw: string): string {
  const trimmed = raw.replace(/[\s\-().]/g, '');
  if (trimmed.startsWith('+')) return trimmed;
  // Default to Spain if no country code is provided.
  if (/^\d{9}$/.test(trimmed)) return `+34${trimmed}`;
  return trimmed.startsWith('00') ? `+${trimmed.slice(2)}` : trimmed;
}

@Injectable()
export class PatientsService {
  constructor(
    @InjectRepository(Patient)
    private readonly repo: Repository<Patient>,
    private readonly events: EventsService,
  ) {}

  async findAll(search?: string): Promise<Patient[]> {
    if (search && search.trim()) {
      const q = `%${search.trim()}%`;
      return this.repo.find({
        where: [{ name: ILike(q) }, { phone: ILike(q) }, { email: ILike(q) }],
        order: { name: 'ASC' },
      });
    }
    return this.repo.find({ order: { name: 'ASC' } });
  }

  async findOne(id: string): Promise<Patient> {
    const patient = await this.repo.findOne({
      where: { id },
      relations: { appointments: true },
      order: { appointments: { startsAt: 'DESC' } },
    });
    if (!patient) throw new NotFoundException('Paciente no encontrado');
    return patient;
  }

  async findByPhone(phone: string): Promise<Patient | null> {
    return this.repo.findOne({ where: { phone: normalizePhone(phone) } });
  }

  async create(dto: CreatePatientDto): Promise<Patient> {
    const patient = this.repo.create({
      ...dto,
      phone: normalizePhone(dto.phone),
      email: dto.email ?? null,
      notes: dto.notes ?? null,
    });
    const saved = await this.repo.save(patient);
    this.events.emit('patient.changed', { id: saved.id });
    return saved;
  }

  async update(id: string, dto: UpdatePatientDto): Promise<Patient> {
    const patient = await this.findOne(id);
    if (dto.name !== undefined) patient.name = dto.name;
    if (dto.phone !== undefined) patient.phone = normalizePhone(dto.phone);
    if (dto.email !== undefined) patient.email = dto.email || null;
    if (dto.notes !== undefined) patient.notes = dto.notes || null;
    const saved = await this.repo.save(patient);
    this.events.emit('patient.changed', { id });
    return saved;
  }

  async remove(id: string): Promise<void> {
    const patient = await this.findOne(id);
    await this.repo.remove(patient);
    this.events.emit('patient.changed', { id });
  }

  /** Upsert by phone, used by the WhatsApp webhook for unknown senders. */
  async upsertByPhone(phone: string, name?: string): Promise<Patient> {
    const normalized = normalizePhone(phone);
    let patient = await this.repo.findOne({ where: { phone: normalized } });
    if (!patient) {
      patient = this.repo.create({
        phone: normalized,
        name: name?.trim() || `WhatsApp ${normalized}`,
        email: null,
        notes: null,
      });
      patient = await this.repo.save(patient);
      this.events.emit('patient.changed', { id: patient.id });
    }
    return patient;
  }

  async count(): Promise<number> {
    return this.repo.count();
  }
}
